"""Tablero de la comunidad: totales de la semana, sin nada que identifique a nadie."""
import json
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import comunidad, cuentas, demo, desenlaces, reportes
from app.config import ajustes
from app.main import app

H = {"X-Centinela": "1"}
PIN = "482915"


@pytest.fixture(autouse=True)
def base_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(ajustes, "base_datos", str(tmp_path / "prueba.db"))
    cuentas.limite_credenciales.reiniciar()
    comunidad.limite_tablero.reiniciar()


def _persona(alias):
    c = TestClient(app)
    assert c.post("/cuenta/registro", json={"alias": alias, "pin": PIN}, headers=H).status_code == 201
    return c


def _tablero():
    r = TestClient(app).get("/comunidad/tablero")
    assert r.status_code == 200 and r.headers["cache-control"] == "no-store"
    return r.json()


def test_vacio_sin_reportes():
    t = _tablero()
    assert t["estafa"] == 0 and t["numeros"] == 0 and t["modalidades"] == [] and t["ejemplo"] == 0


def test_se_mueve_apenas_alguien_reporta_aunque_la_cuenta_sea_nueva():
    # En la demostración los jurados crean cuentas en el momento: su reporte debe verse ya
    c = _persona("jurado-1")
    assert c.post("/reportes", json={"numero": "300 555 0001", "resultado": "intento", "categoria": "suplanta_entidad"},
                  headers=H).status_code == 201
    t = _tablero()
    assert t["estafa"] == 1 and t["intento"] == 1 and t["numeros"] == 1
    assert t["modalidades"] == [{"id": "suplanta_entidad", "nombre": "Falso banco o entidad", "reportes": 1}]


def test_separa_publicidad_y_ordena_modalidades():
    for i, (resultado, categoria) in enumerate([
        ("intento", "premio_falso"), ("perdida", "premio_falso"), ("intento", "suplanta_entidad"), ("publicidad", None),
    ]):
        cuerpo = {"numero": f"300 555 000{i}", "resultado": resultado}
        if categoria:
            cuerpo["categoria"] = categoria
        assert _persona(f"persona-{i}").post("/reportes", json=cuerpo, headers=H).status_code == 201
    t = _tablero()
    assert (t["estafa"], t["perdida"], t["intento"], t["publicidad"]) == (3, 1, 2, 1)
    assert [m["id"] for m in t["modalidades"]] == ["premio_falso", "suplanta_entidad"]


def test_solo_la_ultima_semana():
    _persona("persona-vieja").post("/reportes", json={"numero": "300 555 0009", "resultado": "intento", "categoria": "extorsion"},
                       headers=H)
    con = sqlite3.connect(ajustes.base_datos)
    con.execute("UPDATE reportes SET creado = creado - 8 * 86400")
    con.commit()
    con.close()
    assert _tablero()["estafa"] == 0


def test_no_dice_quien_ni_que_numero():
    _persona("alguien-reconocible").post(
        "/reportes", json={"numero": "300 555 4321", "resultado": "perdida", "categoria": "familiar_falso"}, headers=H)
    texto = json.dumps(_tablero())
    for dato in ("alguien-reconocible", "4321", "3005554321", "573005554321"):
        assert dato not in texto


def test_dice_cuantos_son_de_ejemplo():
    demo.sembrar()
    t = _tablero()
    assert t["ejemplo"] == 8 and t["estafa"] == 6 and t["publicidad"] == 2


def test_cuenta_quienes_no_cayeron_tras_un_aviso():
    desenlaces.guardar("critico", True, "intento")
    desenlaces.guardar("critico", True, "intento")
    desenlaces.guardar("bajo", False, "intento")
    assert _tablero()["avisos"] == {"no_cayeron": 2, "perdieron": 0}


def test_la_pagina_esta_enlazada_y_se_actualiza_sola():
    c = TestClient(app)
    assert 'href="/comunidad.html"' in c.get("/").text
    html = c.get("/comunidad.html").text
    assert '<script src="/comunidad.js" defer></script>' in html and "Solo totales" in html
    js = c.get("/comunidad.js").text
    assert '"/comunidad/tablero"' in js and "setInterval" in js and "innerHTML" not in js
