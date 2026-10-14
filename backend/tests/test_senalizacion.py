import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app import senalizacion
from app.main import app

cliente = TestClient(app)
UNIRSE = {"tipo": "unirse", "consentimiento": True}


@pytest.fixture(autouse=True)
def salas_limpias():
    senalizacion.salas.clear()
    yield
    senalizacion.salas.clear()


def _sala():
    r = cliente.post("/salas")
    assert r.status_code == 201
    return r.json()["codigo"]


def test_codigo_facil_de_dictar():
    codigo = _sala()
    assert len(codigo) == 6 and all(c in senalizacion.ALFABETO for c in codigo)
    assert cliente.get(f"/salas/{codigo.lower()}").json()["roles_libres"] == ["llama", "recibe"]


def test_sala_inexistente():
    assert cliente.get("/salas/NOEXIS").status_code == 404


def test_dos_participantes_se_conectan_y_reenvian_mensajes():
    codigo = _sala()
    with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=recibe") as recibe:
        recibe.send_json(UNIRSE)
        assert recibe.receive_json() == {"tipo": "unido", "rol": "recibe"}
        assert cliente.get(f"/salas/{codigo}").json()["roles_libres"] == ["llama"]
        with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=llama") as llama:
            llama.send_json(UNIRSE)
            assert llama.receive_json()["tipo"] == "unido"
            assert llama.receive_json() == {"tipo": "listos"}
            assert recibe.receive_json() == {"tipo": "listos"}

            llama.send_json({"tipo": "oferta", "sdp": "v=0"})
            assert recibe.receive_json() == {"tipo": "oferta", "sdp": "v=0"}
            recibe.send_json({"tipo": "respuesta", "sdp": "v=0"})
            assert llama.receive_json()["tipo"] == "respuesta"
            llama.send_json({"tipo": "texto", "texto": "Necesito el código"})
            assert recibe.receive_json()["texto"] == "Necesito el código"
        # Al irse uno, el otro se entera
        assert recibe.receive_json() == {"tipo": "colgo"}


def test_mensajes_de_tipo_desconocido_no_se_reenvian():
    codigo = _sala()
    with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=recibe") as recibe:
        recibe.send_json(UNIRSE)
        recibe.receive_json()
        with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=llama") as llama:
            llama.send_json(UNIRSE)
            llama.receive_json(), llama.receive_json(), recibe.receive_json()
            llama.send_json({"tipo": "inventado", "x": 1})
            llama.send_json({"tipo": "texto", "texto": "hola"})
            assert recibe.receive_json() == {"tipo": "texto", "texto": "hola"}


def test_sin_consentimiento_no_entra():
    codigo = _sala()
    with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=recibe") as ws:
        ws.send_json({"tipo": "unirse", "consentimiento": False})
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()
    assert e.value.code == 4401


def test_rol_ocupado_o_invalido():
    codigo = _sala()
    with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=recibe") as primero:
        primero.send_json(UNIRSE)
        primero.receive_json()
        with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=recibe") as segundo:
            segundo.send_json(UNIRSE)
            with pytest.raises(WebSocketDisconnect) as e:
                segundo.receive_json()
        assert e.value.code == 4409
    with pytest.raises(WebSocketDisconnect) as e:
        with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=admin") as ws:
            ws.receive_json()
    assert e.value.code == 4403


def test_rechaza_otro_origen():
    codigo = _sala()
    with pytest.raises(WebSocketDisconnect) as e:
        with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=llama", headers={"origin": "https://malicioso.example"}) as ws:
            ws.receive_json()
    assert e.value.code == 4403


def test_mensaje_demasiado_grande_cierra_la_conexion():
    codigo = _sala()
    with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=llama") as ws:
        ws.send_json(UNIRSE)
        ws.receive_json()
        ws.send_text("x" * (senalizacion.MAX_MENSAJE + 1))
        with pytest.raises(WebSocketDisconnect) as e:
            ws.receive_json()
    assert e.value.code == 4413


def test_la_sala_desaparece_cuando_todos_cuelgan():
    codigo = _sala()
    with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=llama") as ws:
        ws.send_json(UNIRSE)
        ws.receive_json()
    assert codigo not in senalizacion.salas


def test_limite_de_salas(monkeypatch):
    monkeypatch.setattr(senalizacion, "MAX_SALAS", 2)
    _sala(), _sala()
    assert cliente.post("/salas").status_code == 429
