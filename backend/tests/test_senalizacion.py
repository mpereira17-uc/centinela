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
        unido = recibe.receive_json()
        assert unido["tipo"] == "unido" and unido["rol"] == "recibe" and unido["reconexion"] is False
        assert len(unido["llave"]) >= 16
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


# ---- Cortes de conexión sin colgar ----


def _unir(rol, codigo, llave=None):
    ws = cliente.websocket_connect(f"/salas/{codigo}/ws?rol={rol}").__enter__()
    ws.send_json(UNIRSE | ({"llave": llave} if llave else {}))
    return ws


def _llamada_en_curso():
    codigo = _sala()
    recibe = _unir("recibe", codigo)
    llave_recibe = recibe.receive_json()["llave"]
    llama = _unir("llama", codigo)
    llave_llama = llama.receive_json()["llave"]
    assert llama.receive_json() == {"tipo": "listos"}
    assert recibe.receive_json() == {"tipo": "listos"}
    return codigo, recibe, llave_recibe, llama, llave_llama


def _cortar(ws):
    # Un corte de red llega como cierre anormal, no como el cierre normal de quien se va
    ws.close(code=1006)
    ws.__exit__(None, None, None)


def test_un_corte_no_termina_la_llamada_y_se_puede_volver():
    codigo, recibe, _, llama, llave_llama = _llamada_en_curso()
    _cortar(llama)
    assert recibe.receive_json() == {"tipo": "reconectando", "segundos": senalizacion.GRACIA}
    # Mientras tanto nadie más puede tomar ese papel
    assert cliente.get(f"/salas/{codigo}").json()["roles_libres"] == []

    llama = _unir("llama", codigo, llave_llama)
    unido = llama.receive_json()
    assert unido == {"tipo": "unido", "rol": "llama", "llave": llave_llama, "reconexion": True}
    assert recibe.receive_json() == {"tipo": "volvio"}
    # No se vuelve a empezar la llamada: los mensajes siguen pasando
    llama.send_json({"tipo": "oferta", "sdp": "v=0 reinicio"})
    assert recibe.receive_json() == {"tipo": "oferta", "sdp": "v=0 reinicio"}
    llama.__exit__(None, None, None)
    recibe.__exit__(None, None, None)


def test_sin_la_llave_no_se_ocupa_el_lugar_de_quien_se_cayo():
    codigo, recibe, _, llama, _ = _llamada_en_curso()
    _cortar(llama)
    recibe.receive_json()
    intruso = _unir("llama", codigo)
    with pytest.raises(WebSocketDisconnect) as e:
        intruso.receive_json()
    assert e.value.code == 4409
    falsa = _unir("llama", codigo, "llave-inventada")
    with pytest.raises(WebSocketDisconnect) as e:
        falsa.receive_json()
    assert e.value.code == 4410
    recibe.__exit__(None, None, None)


def test_pasado_el_tiempo_de_gracia_el_lugar_se_libera(monkeypatch):
    codigo, recibe, _, llama, llave_llama = _llamada_en_curso()
    monkeypatch.setattr(senalizacion, "GRACIA", -1)
    _cortar(llama)
    recibe.receive_json()
    assert cliente.get(f"/salas/{codigo}").json()["roles_libres"] == ["llama"]
    tarde = _unir("llama", codigo, llave_llama)
    with pytest.raises(WebSocketDisconnect) as e:
        tarde.receive_json()
    assert e.value.code == 4410
    recibe.__exit__(None, None, None)


def test_quien_vuelve_reemplaza_la_conexion_vieja_que_el_servidor_no_vio_caer():
    codigo, recibe, _, llama, llave_llama = _llamada_en_curso()
    nueva = _unir("llama", codigo, llave_llama)
    assert nueva.receive_json()["reconexion"] is True
    assert recibe.receive_json() == {"tipo": "volvio"}
    with pytest.raises(WebSocketDisconnect) as e:
        llama.receive_json()
    assert e.value.code == 4000
    nueva.send_json({"tipo": "texto", "texto": "sigo aquí"})
    assert recibe.receive_json() == {"tipo": "texto", "texto": "sigo aquí"}
    nueva.__exit__(None, None, None)
    recibe.__exit__(None, None, None)


def test_colgar_si_termina_la_llamada_de_una_vez():
    codigo, recibe, _, llama, llave_llama = _llamada_en_curso()
    llama.send_json({"tipo": "colgar"})
    assert recibe.receive_json() == {"tipo": "colgar"}
    assert recibe.receive_json() == {"tipo": "colgo"}
    llama.__exit__(None, None, None)
    otra = _unir("llama", codigo, llave_llama)
    with pytest.raises(WebSocketDisconnect) as e:
        otra.receive_json()
    assert e.value.code == 4410
    recibe.__exit__(None, None, None)
    assert codigo not in senalizacion.salas


def test_mantener_viva_la_conexion_y_pedir_reinicio():
    _, recibe, _, llama, _ = _llamada_en_curso()
    recibe.send_json({"tipo": "ping"})
    assert recibe.receive_json() == {"tipo": "pong"}
    # El ping no se reenvía; pedir reiniciar el audio sí
    recibe.send_json({"tipo": "reiniciar"})
    assert llama.receive_json() == {"tipo": "reiniciar"}
    llama.__exit__(None, None, None)
    recibe.__exit__(None, None, None)


def test_si_quien_recibe_se_cae_antes_de_empezar_la_llamada_empieza_al_volver():
    codigo = _sala()
    recibe = _unir("recibe", codigo)
    llave = recibe.receive_json()["llave"]
    _cortar(recibe)
    llama = _unir("llama", codigo)
    llama.receive_json()
    assert llama.receive_json() == {"tipo": "reconectando", "segundos": senalizacion.GRACIA}
    recibe = _unir("recibe", codigo, llave)
    assert recibe.receive_json()["reconexion"] is True
    assert recibe.receive_json() == {"tipo": "listos"}
    assert llama.receive_json() == {"tipo": "listos"}
    llama.__exit__(None, None, None)
    recibe.__exit__(None, None, None)
