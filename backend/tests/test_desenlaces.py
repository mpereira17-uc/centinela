"""¿Cómo terminó? El feedback de un toque al colgar y el reporte que deduce la categoría."""
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import cuentas, reportes
from app.config import ajustes
from app.main import app

H = {"X-Centinela": "1"}
NUMERO = "300 765 4321"


@pytest.fixture(autouse=True)
def base_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(ajustes, "base_datos", str(tmp_path / "prueba.db"))
    cuentas.limite_credenciales.reiniciar()
    reportes.limite_consultas.reiniciar()


def _llamada(c, frases, numero=None):
    llamada = c.post("/llamadas", json={"numero": numero} if numero else {}).json()
    for i, texto in enumerate(frases):
        c.post(f"/llamadas/{llamada['id']}/fragmentos", json={"texto": texto, "inicio": i * 3, "fin": i * 3 + 2})
    return llamada["id"]


ESTAFA = ["Le hablamos del banco, su cuenta va a quedar bloqueada.", "Dícteme el código que le llegó, es urgente."]


def test_cuenta_el_desenlace_una_sola_vez_y_sin_datos_personales():
    c = TestClient(app)
    lid = _llamada(c, ESTAFA)
    r = c.post(f"/llamadas/{lid}/desenlace", json={"resultado": "intento"})
    assert r.status_code == 201
    assert r.json()["aviso"] is True and r.json()["nivel_max"] == "critico"
    assert r.json()["categoria_sugerida"] == "suplanta_entidad"
    assert c.post(f"/llamadas/{lid}/desenlace", json={"resultado": "legitima"}).status_code == 409
    con = sqlite3.connect(ajustes.base_datos)
    columnas = [f[1] for f in con.execute("PRAGMA table_info(desenlaces)")]
    con.close()
    assert columnas == ["id", "creado", "nivel_max", "aviso", "resultado"]


def test_valida_el_resultado_y_la_llamada():
    c = TestClient(app)
    lid = _llamada(c, ["Hola"])
    assert c.post(f"/llamadas/{lid}/desenlace", json={"resultado": "otra_cosa"}).status_code == 422
    assert c.post("/llamadas/no-existe/desenlace", json={"resultado": "intento"}).status_code == 404


def test_el_resumen_cuenta_aciertos_y_falsas_alarmas():
    c = TestClient(app)
    c.post(f"/llamadas/{_llamada(c, ESTAFA)}/desenlace", json={"resultado": "perdida"})
    c.post(f"/llamadas/{_llamada(c, ESTAFA)}/desenlace", json={"resultado": "legitima"})
    c.post(f"/llamadas/{_llamada(c, ['Hola, ¿cómo está la abuela?'])}/desenlace", json={"resultado": "intento"})
    c.post(f"/llamadas/{_llamada(c, ['Te llamo para el almuerzo'])}/desenlace", json={"resultado": "legitima"})
    r = c.get("/desenlaces/resumen").json()
    assert r["total"] == 4
    assert r["tabla"] == {"con_aviso": {"estafa": 1, "no_estafa": 1}, "sin_aviso": {"estafa": 1, "no_estafa": 1}}
    assert r["estafas_avisadas"] == 0.5 and r["falsas_alarmas"] == 0.5


def test_reporte_de_un_toque_deduce_la_categoria_de_la_llamada():
    c = TestClient(app)
    assert c.post("/cuenta/registro", json={"alias": "persona_toque", "pin": "482915"}, headers=H).status_code == 201
    lid = _llamada(c, ["Si no paga la vacuna le caemos al negocio, consigne hoy mismo."], numero=NUMERO)
    r = c.post("/reportes", json={"numero": NUMERO, "resultado": "intento", "llamada_id": lid}, headers=H)
    assert r.status_code == 201
    assert r.json()["respaldado"] is True
    con = sqlite3.connect(ajustes.base_datos)
    assert con.execute("SELECT categoria FROM reportes").fetchone()[0] == "extorsion"
    con.close()


def test_sin_llamada_la_categoria_sigue_siendo_obligatoria():
    c = TestClient(app)
    assert c.post("/cuenta/registro", json={"alias": "persona_sin", "pin": "482915"}, headers=H).status_code == 201
    assert c.post("/reportes", json={"numero": NUMERO, "resultado": "intento"}, headers=H).status_code == 422


def test_la_pantalla_de_llamada_pregunta_como_termino():
    c = TestClient(app)
    html = c.get("/llamada.html").text
    for r in ("perdida", "intento", "legitima", "publicidad"):
        assert f'data-resultado="{r}"' in html
    assert "/desenlace" in c.get("/llamada.js").text
