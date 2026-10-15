"""Base estructurada de guiones: plantillas, guiones sintéticos y la API de solo lectura."""
import json

import pytest
from fastapi.testclient import TestClient

from app import base_guiones
from app.main import app
from evaluacion import entrenar, generar_guiones, guiones


@pytest.fixture(autouse=True)
def sin_limite():
    base_guiones.limite_guiones.reiniciar()


def test_el_archivo_sintetico_esta_al_dia_con_las_plantillas():
    # Si falla: python -m evaluacion.generar_guiones
    assert guiones.RUTA_SINTETICOS.read_text(encoding="utf-8") == generar_guiones.como_texto(generar_guiones.generar())


def test_una_llamada_por_plantilla_y_region_sin_huecos_sin_llenar():
    datos = json.loads(generar_guiones.PLANTILLAS.read_text(encoding="utf-8"))
    sinteticos = [g for g in guiones.cargar() if g.fuente == "plantilla"]
    assert len(sinteticos) == len(datos["plantillas"]) * len(datos["regiones"])
    assert {g.region for g in sinteticos} == set(datos["regiones"])
    for g in sinteticos:
        assert all("{" not in t.texto and "}" not in t.texto for t in g.turnos), g.id
    # Las de prueba quedan balanceadas para medir detección y falsas alertas por igual
    prueba = [g for g in sinteticos if g.particion == "sintetica_prueba"]
    assert sum(g.es_riesgo for g in prueba) == len(prueba) / 2


def test_es_reproducible():
    assert generar_guiones.generar() == generar_guiones.generar()


def test_ninguna_plantilla_de_prueba_entra_al_entrenamiento():
    textos, _, grupos = entrenar.ejemplos_con_grupos()
    de_prueba = [g for g in guiones.cargar() if g.particion in ("sintetica_prueba", "regional", "reservada")]
    # Las despedidas sueltas ("Listo, hablamos.") se repiten entre plantillas y no dicen nada del riesgo
    datos = json.loads(generar_guiones.PLANTILLAS.read_text(encoding="utf-8"))
    despedidas = {f"{d}." for r in datos["regiones"].values() for d in r["despedida"]}
    assert not ({t.texto for g in de_prueba for t in g.turnos} & set(textos)) - despedidas
    plantillas_prueba = {g.plantilla for g in de_prueba if g.plantilla}
    assert not {f"plantilla-{p}" for p in plantillas_prueba} & set(grupos)


def test_la_api_filtra_y_pagina():
    c = TestClient(app)
    r = c.get("/guiones", params={"region": "bogota", "etiqueta": "riesgo", "limite": 3})
    assert r.status_code == 200
    datos = r.json()
    assert datos["total"] > 3 and len(datos["guiones"]) == 3
    g = datos["guiones"][0]
    assert g["region"] == "bogota" and g["etiqueta"] == "riesgo"
    assert g["turnos"][0].keys() == {"hablante", "texto"}
    siguiente = c.get("/guiones", params={"region": "bogota", "etiqueta": "riesgo", "limite": 3, "desde": 3}).json()
    assert siguiente["guiones"][0]["id"] != g["id"]
    assert c.get("/guiones", params={"particion": "inventada"}).status_code == 422
    assert c.get("/guiones", params={"limite": 500}).status_code == 422


def test_la_api_resume_y_publica_el_esquema():
    c = TestClient(app)
    resumen = c.get("/guiones/resumen").json()
    assert resumen["total"] == len(guiones.cargar())
    assert resumen["por_fuente"]["plantilla"] > resumen["por_fuente"]["escrito"]
    assert resumen["para_entrenar"] == ["desarrollo", "sintetica_desarrollo"]
    esquema = c.get("/guiones/esquema").json()
    assert set(esquema["properties"]["particion"]["enum"]) == set(guiones.PARTICIONES)
    assert set(esquema["properties"]["fuente"]["enum"]) == set(guiones.FUENTES)


def test_valida_la_fuente(tmp_path):
    malo = [{"id": "x", "etiqueta": "legitima", "particion": "desarrollo", "fuente": "internet",
             "turnos": [["llamante", "hola"]]}]
    ruta = tmp_path / "g.json"
    ruta.write_text(json.dumps(malo), encoding="utf-8")
    with pytest.raises(guiones.GuionInvalido):
        guiones.cargar(ruta)
