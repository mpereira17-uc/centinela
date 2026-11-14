from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def _chequeo(**respuestas):
    r = cliente.post("/chequeo", json=respuestas)
    assert r.status_code == 200
    return r.json()


def test_sin_senales_no_avisa():
    r = _chequeo(codigo=False, plata=False, presion=False)
    assert r["decision"]["nivel"] == "bajo" and not r["mostrar_aviso"]


def test_solo_presion_pide_cuidado_sin_aviso():
    # Un jefe con prisa o un familiar que pide reserva no basta para alarmar
    r = _chequeo(presion=True)
    assert r["decision"]["nivel"] == "moderado" and not r["mostrar_aviso"]


def test_pedir_codigo_es_riesgo_alto():
    r = _chequeo(codigo=True)
    assert r["decision"]["nivel"] == "alto" and r["mostrar_aviso"]
    assert "código" in r["decision"]["mensaje"]


def test_plata_con_presion_es_critico():
    r = _chequeo(plata=True, presion=True)
    d = r["decision"]
    assert d["nivel"] == "critico" and r["mostrar_aviso"]
    # El aviso empieza por lo más grave: la petición, no la prisa
    assert d["mensaje"].startswith("RIESGO CRÍTICO. Te piden plata")
    assert {s["id"] for s in d["senales"]} == {"plata_declarada", "presion_declarada"}


def test_respuestas_vacias_cuentan_como_no():
    assert _chequeo()["decision"]["nivel"] == "bajo"


def test_rechaza_respuestas_que_no_son_si_o_no():
    assert cliente.post("/chequeo", json={"codigo": "tal vez"}).status_code == 422
