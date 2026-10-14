import json
import logging
import sqlite3
import time

import pytest
from fastapi.testclient import TestClient

from app import cuentas
from app.config import ajustes
from app.main import app

H = {"X-Centinela": "1"}
PIN = "482915"
CODIGO = "Le hablamos del banco, necesito el código que le llegó."


@pytest.fixture(autouse=True)
def base_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(ajustes, "base_datos", str(tmp_path / "prueba.db"))
    cuentas.limite_credenciales.reiniciar()


def _persona(alias="ana", guardar=True):
    c = TestClient(app)
    assert c.post("/cuenta/registro", json={"alias": alias, "pin": PIN}, headers=H).status_code == 201
    if guardar:
        c.put("/cuenta/consentimientos", json={"finalidad": "guardar_historial", "otorgado": True}, headers=H)
    return c


def _conversar(c, frases=(CODIGO,)):
    llamada = c.post("/llamadas").json()
    for i, texto in enumerate(frases):
        r = c.post(f"/llamadas/{llamada['id']}/fragmentos", json={"texto": texto, "inicio": i, "fin": i + 1})
        assert r.status_code == 200
    return llamada


def test_sin_cuenta_no_se_guarda_nada():
    llamada = _conversar(TestClient(app))
    assert llamada["guardada"] is False
    assert "dueno" not in llamada


def test_con_cuenta_pero_sin_permiso_no_se_guarda():
    c = _persona(guardar=False)
    assert _conversar(c)["guardada"] is False
    assert c.get("/historial").json()["llamadas"] == []


def test_con_permiso_se_guarda_con_su_nivel_maximo():
    c = _persona()
    llamada = _conversar(c, ["Buenas tardes.", CODIGO, "Gracias."])
    assert llamada["guardada"] is True

    h = c.get("/historial").json()
    assert h["dias_retencion"] == ajustes.dias_retencion
    [resumen] = h["llamadas"]
    assert resumen["id"] == llamada["id"]
    assert resumen["frases"] == 3
    assert resumen["nivel_max"] in ("alto", "critico")
    assert resumen["aviso_visible"] is True

    detalle = c.get(f"/historial/{llamada['id']}").json()
    assert [f["texto"] for f in detalle["fragmentos"]] == ["Buenas tardes.", CODIGO, "Gracias."]
    assert detalle["fragmentos"][1]["decisiones"]


def test_nadie_mas_ve_ni_usa_la_llamada_guardada():
    ana = _persona()
    llamada = _conversar(ana)
    beto = _persona("beto")
    anonimo = TestClient(app)
    for c in (beto, anonimo):
        assert c.get(f"/llamadas/{llamada['id']}").status_code == 404
        assert c.post(f"/llamadas/{llamada['id']}/fragmentos", json={"texto": "hola", "inicio": 9, "fin": 10}).status_code == 404
        assert c.post("/asistente", json={"texto": "¿parece estafa?", "llamada_id": llamada["id"]}).status_code == 404
    assert beto.get(f"/historial/{llamada['id']}").status_code == 404
    assert beto.delete(f"/historial/{llamada['id']}", headers=H).status_code == 404
    assert anonimo.get("/historial").status_code == 401
    assert ana.get(f"/historial/{llamada['id']}").status_code == 200


def test_borrar_una_conversacion_detiene_su_guardado():
    c = _persona()
    llamada = _conversar(c)
    assert c.delete(f"/historial/{llamada['id']}", headers=H).json() == {"borradas": 1}
    # La conversación sigue activa en pantalla, pero ya no vuelve al historial
    c.post(f"/llamadas/{llamada['id']}/fragmentos", json={"texto": "otra frase", "inicio": 5, "fin": 6})
    assert c.get("/historial").json()["llamadas"] == []
    assert c.get(f"/llamadas/{llamada['id']}").json()["guardada"] is False


def test_borrar_todo_el_historial():
    c = _persona()
    _conversar(c)
    _conversar(c)
    assert c.delete("/historial", headers=H).json() == {"borradas": 2}
    con = sqlite3.connect(ajustes.base_datos)
    assert con.execute("SELECT COUNT(*) FROM fragmentos_guardados").fetchone()[0] == 0


def test_borrar_exige_cabecera():
    c = _persona()
    assert c.delete("/historial").status_code == 403


def test_retirar_el_permiso_borra_el_historial():
    c = _persona()
    _conversar(c)
    c.put("/cuenta/consentimientos", json={"finalidad": "guardar_historial", "otorgado": False}, headers=H)
    assert c.get("/historial").json()["llamadas"] == []
    assert _conversar(c)["guardada"] is False


def test_retencion_borra_lo_vencido():
    c = _persona()
    vieja = _conversar(c)
    _conversar(c)
    hace_mucho = time.time() - (ajustes.dias_retencion + 1) * 86400
    con = sqlite3.connect(ajustes.base_datos)
    con.execute("UPDATE llamadas_guardadas SET actualizada = ? WHERE id = ?", (hace_mucho, vieja["id"]))
    con.commit()
    ids = [l["id"] for l in c.get("/historial").json()["llamadas"]]
    assert vieja["id"] not in ids and len(ids) == 1
    assert con.execute("SELECT COUNT(*) FROM fragmentos_guardados WHERE llamada_id = ?", (vieja["id"],)).fetchone()[0] == 0


def test_exportar_todos_los_datos():
    c = _persona()
    _conversar(c)
    r = c.get("/cuenta/exportar")
    assert r.status_code == 200
    assert "attachment" in r.headers["content-disposition"]
    assert r.headers["cache-control"] == "no-store"
    datos = r.json()
    assert datos["cuenta"]["alias"] == "ana"
    assert any(p["finalidad"] == "guardar_historial" and p["otorgado"] for p in datos["permisos"])
    assert datos["historial"][0]["fragmentos"][0]["texto"] == CODIGO
    assert len(datos["sesiones"]) == 1
    # Nada secreto en la exportación
    texto = r.text
    assert PIN not in texto and "argon2" not in texto and c.cookies.get("centinela_sesion") not in texto


def test_eliminar_la_cuenta_borra_el_historial():
    c = _persona()
    _conversar(c)
    c.post("/cuenta/eliminar", json={"pin": PIN}, headers=H)
    con = sqlite3.connect(ajustes.base_datos)
    assert con.execute("SELECT COUNT(*) FROM llamadas_guardadas").fetchone()[0] == 0
    assert con.execute("SELECT COUNT(*) FROM fragmentos_guardados").fetchone()[0] == 0


def test_logs_sin_texto_de_la_conversacion(caplog):
    c = _persona()
    with caplog.at_level(logging.INFO, logger="centinela"):
        _conversar(c)
        c.get("/cuenta/exportar")
    assert "código" not in caplog.text and "banco" not in caplog.text


def test_el_historial_guarda_json_valido():
    c = _persona()
    _conversar(c)
    con = sqlite3.connect(ajustes.base_datos)
    datos, = con.execute("SELECT datos FROM fragmentos_guardados").fetchone()
    assert json.loads(datos)["texto"] == CODIGO
