import logging

from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def _nueva_llamada():
    llamada = cliente.post("/llamadas").json()
    return f"/llamadas/{llamada['id']}/fragmentos"


def test_salud():
    r = cliente.get("/salud")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"


def test_catalogo_publico_de_senales():
    r = cliente.get("/senales")
    assert r.status_code == 200
    assert any(s["id"] == "pide_codigo" for s in r.json())


def test_llamada_de_riesgo_dispara_un_solo_aviso():
    url = _nueva_llamada()

    r1 = cliente.post(url, json={"texto": "Buenas tardes, le hablamos del banco.", "inicio": 0, "fin": 3})
    assert r1.json()["mostrar_aviso"] is False
    assert r1.json()["decision_visible"]["nivel"] == "moderado"

    r2 = cliente.post(url, json={"texto": "Dígame el código que le llegó.", "inicio": 3, "fin": 6})
    assert r2.json()["mostrar_aviso"] is True
    assert r2.json()["decision_visible"]["nivel"] == "alto"
    assert r2.json()["decision_visible"]["fuente"] == "contenido"

    r3 = cliente.post(url, json={"texto": "Es urgente, hay un bloqueo en su cuenta.", "inicio": 6, "fin": 9})
    assert r3.json()["mostrar_aviso"] is False  # no se duplica el aviso
    assert r3.json()["decision_visible"]["nivel"] == "critico"

    decisiones = r3.json()["fragmento"]["decisiones"]
    assert {d["estrategia"] for d in decisiones} == {"por_fragmento", "acumulacion", "hibrida"}


def test_acumulacion_ve_indicios_que_por_fragmento_no_ve():
    url = _nueva_llamada()
    cliente.post(url, json={"texto": "Dígame el código que le llegó.", "inicio": 0, "fin": 3})
    r = cliente.post(url, json={"texto": "Rápido, por favor.", "inicio": 3, "fin": 5})
    niveles = {d["estrategia"]: d["nivel"] for d in r.json()["fragmento"]["decisiones"]}
    assert niveles["por_fragmento"] == "moderado" and niveles["acumulacion"] == "critico"


def test_llamada_legitima_no_alerta():
    url = _nueva_llamada()
    r = cliente.post(url, json={"texto": "Hola mamá, ¿vienes a almorzar el domingo?", "inicio": 0, "fin": 3})
    assert r.json()["mostrar_aviso"] is False
    assert r.json()["decision_visible"]["nivel"] == "bajo"


def test_rechaza_entradas_invalidas():
    url = _nueva_llamada()
    assert cliente.post(url, json={"texto": "", "inicio": 0, "fin": 1}).status_code == 422
    assert cliente.post(url, json={"texto": "x" * 2001, "inicio": 0, "fin": 1}).status_code == 422
    assert cliente.post(url, json={"texto": "hola", "inicio": 5, "fin": 1}).status_code == 422


def test_llamada_inexistente():
    r = cliente.post("/llamadas/no-existe/fragmentos", json={"texto": "hola", "inicio": 0, "fin": 1})
    assert r.status_code == 404


def test_los_logs_no_guardan_el_texto_de_la_conversacion(caplog):
    url = _nueva_llamada()
    with caplog.at_level(logging.INFO, logger="centinela"):
        cliente.post(url, json={"texto": "Mi clave es 4821", "inicio": 0, "fin": 2})
    assert caplog.records, "se esperaba al menos un registro"
    assert "4821" not in caplog.text
    assert "clave" not in caplog.text
