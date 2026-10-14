from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_salud():
    r = cliente.get("/salud")
    assert r.status_code == 200
    assert r.json()["estado"] == "ok"


def test_llamada_de_riesgo_dispara_un_solo_aviso():
    llamada = cliente.post("/llamadas").json()
    url = f"/llamadas/{llamada['id']}/fragmentos"

    r1 = cliente.post(url, json={"texto": "Buenas tardes, le hablamos del banco.", "inicio": 0, "fin": 3})
    assert r1.json()["mostrar_aviso"] is False

    r2 = cliente.post(url, json={"texto": "Es urgente, hay un bloqueo en su cuenta.", "inicio": 3, "fin": 6})
    assert r2.json()["mostrar_aviso"] is True

    r3 = cliente.post(url, json={"texto": "Dígame el código que le llegó.", "inicio": 6, "fin": 9})
    assert r3.json()["mostrar_aviso"] is False  # no se duplica el aviso

    decisiones = r3.json()["fragmento"]["decisiones"]
    assert {d["estrategia"] for d in decisiones} == {"por_fragmento", "acumulacion"}


def test_llamada_legitima_no_alerta():
    llamada = cliente.post("/llamadas").json()
    r = cliente.post(
        f"/llamadas/{llamada['id']}/fragmentos",
        json={"texto": "Hola mamá, ¿vienes a almorzar el domingo?", "inicio": 0, "fin": 3},
    )
    assert r.json()["mostrar_aviso"] is False
