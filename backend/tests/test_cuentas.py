import logging
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import cuentas
from app.config import ajustes
from app.main import app

H = {"X-Centinela": "1"}
PIN = "482915"


@pytest.fixture(autouse=True)
def base_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(ajustes, "base_datos", str(tmp_path / "prueba.db"))
    cuentas.limite_credenciales.reiniciar()
    yield


@pytest.fixture
def cliente():
    return TestClient(app)


def _registrar(cliente, alias="ana", pin=PIN):
    return cliente.post("/cuenta/registro", json={"alias": alias, "pin": pin}, headers=H)


def test_registro_crea_sesion_con_cookie_segura(cliente):
    r = _registrar(cliente)
    assert r.status_code == 201
    cookie = r.headers["set-cookie"]
    assert "centinela_sesion=" in cookie
    assert "HttpOnly" in cookie
    assert "SameSite=strict" in cookie
    assert "Max-Age=43200" in cookie
    assert cliente.get("/cuenta").json()["alias"] == "ana"


def test_pin_no_se_guarda_en_claro(cliente):
    _registrar(cliente)
    con = sqlite3.connect(ajustes.base_datos)
    pin_hash, = con.execute("SELECT pin_hash FROM usuarios").fetchone()
    token_hash, = con.execute("SELECT token_hash FROM sesiones").fetchone()
    assert PIN not in pin_hash and pin_hash.startswith("$argon2id$")
    assert token_hash != cliente.cookies.get("centinela_sesion")


@pytest.mark.parametrize("pin", ["111111", "123456", "987654", "12345", "abcdef", "1234567890123"])
def test_rechaza_pin_debil_o_invalido(cliente, pin):
    assert _registrar(cliente, pin=pin).status_code == 422


def test_alias_repetido_sin_importar_mayusculas(cliente):
    _registrar(cliente)
    assert _registrar(TestClient(app), alias="ANA").status_code == 409


def test_sin_cabecera_x_centinela_se_rechaza(cliente):
    r = cliente.post("/cuenta/registro", json={"alias": "ana", "pin": PIN})
    assert r.status_code == 403


def test_entrar_con_pin(cliente):
    _registrar(cliente)
    nuevo = TestClient(app)
    r = nuevo.post("/cuenta/entrar", json={"alias": " Ana ", "pin": PIN}, headers=H)
    assert r.status_code == 200
    assert nuevo.get("/cuenta").status_code == 200


def test_mismo_error_para_alias_inexistente_y_pin_errado(cliente):
    _registrar(cliente)
    a = cliente.post("/cuenta/entrar", json={"alias": "ana", "pin": "000001"}, headers=H)
    b = cliente.post("/cuenta/entrar", json={"alias": "nadie", "pin": "000001"}, headers=H)
    assert a.status_code == b.status_code == 401
    assert a.json() == b.json()


def test_bloqueo_tras_cinco_intentos_fallidos(cliente):
    _registrar(cliente)
    for _ in range(cuentas.MAX_INTENTOS):
        assert cliente.post("/cuenta/entrar", json={"alias": "ana", "pin": "000001"}, headers=H).status_code == 401
    # Bloqueada: ni siquiera el PIN correcto entra
    r = cliente.post("/cuenta/entrar", json={"alias": "ana", "pin": PIN}, headers=H)
    assert r.status_code == 429


def test_limite_de_solicitudes_por_cliente(cliente):
    codigos = [
        cliente.post("/cuenta/entrar", json={"alias": f"x{i}", "pin": "1"}, headers=H).status_code for i in range(21)
    ]
    assert codigos[:20] == [401] * 20
    assert codigos[20] == 429


def test_sin_sesion_no_hay_acceso(cliente):
    assert cliente.get("/cuenta").status_code == 401
    assert TestClient(app, cookies={"centinela_sesion": "inventado"}).get("/cuenta").status_code == 401


def test_salir_invalida_el_token(cliente):
    _registrar(cliente)
    token = cliente.cookies.get("centinela_sesion")
    assert cliente.post("/cuenta/salir", headers=H).status_code == 200
    otro = TestClient(app, cookies={"centinela_sesion": token})
    assert otro.get("/cuenta").status_code == 401


def test_revocar_sesion_de_otro_dispositivo(cliente):
    _registrar(cliente)
    celular = TestClient(app, headers={"User-Agent": "Celular de prueba"})
    celular.post("/cuenta/entrar", json={"alias": "ana", "pin": PIN}, headers=H)

    sesiones = cliente.get("/cuenta/sesiones").json()
    assert len(sesiones) == 2
    otra = next(s for s in sesiones if not s["actual"])
    assert otra["dispositivo"] == "Celular de prueba"

    assert cliente.delete(f"/cuenta/sesiones/{otra['id']}", headers=H).status_code == 200
    assert celular.get("/cuenta").status_code == 401
    assert cliente.get("/cuenta").status_code == 200


def test_cerrar_otras_sesiones(cliente):
    _registrar(cliente)
    otro = TestClient(app)
    otro.post("/cuenta/entrar", json={"alias": "ana", "pin": PIN}, headers=H)
    assert cliente.post("/cuenta/sesiones/cerrar-otras", headers=H).json() == {"cerradas": 1}
    assert otro.get("/cuenta").status_code == 401


def test_no_se_puede_cerrar_la_sesion_de_otro_usuario(cliente):
    _registrar(cliente)
    beto = TestClient(app)
    _registrar(beto, alias="beto")
    sesion_beto = beto.get("/cuenta/sesiones").json()[0]["id"]
    assert cliente.delete(f"/cuenta/sesiones/{sesion_beto}", headers=H).status_code == 404
    assert beto.get("/cuenta").status_code == 200


def test_consentimientos_separados_y_apagados_por_defecto(cliente):
    _registrar(cliente)
    consentimientos = cliente.get("/cuenta").json()["consentimientos"]
    assert {c["finalidad"] for c in consentimientos} == set(cuentas.FINALIDADES)
    assert not any(c["otorgado"] for c in consentimientos)

    r = cliente.put("/cuenta/consentimientos", json={"finalidad": "transcripcion_audio", "otorgado": True}, headers=H)
    assert r.status_code == 200
    estado = {c["finalidad"]: c["otorgado"] for c in cliente.get("/cuenta").json()["consentimientos"]}
    assert estado["transcripcion_audio"] is True
    assert estado["entrenamiento_modelos"] is False


def test_autenticacion_vocal_no_se_puede_activar(cliente):
    _registrar(cliente)
    r = cliente.put("/cuenta/consentimientos", json={"finalidad": "autenticacion_vocal", "otorgado": True}, headers=H)
    assert r.status_code == 422
    vocal = next(c for c in cliente.get("/cuenta").json()["consentimientos"] if c["finalidad"] == "autenticacion_vocal")
    assert vocal["disponible"] is False and vocal["otorgado"] is False


def test_eliminar_cuenta_pide_pin_y_borra_todo(cliente):
    _registrar(cliente)
    assert cliente.post("/cuenta/eliminar", json={"pin": "000001"}, headers=H).status_code == 403
    assert cliente.post("/cuenta/eliminar", json={"pin": PIN}, headers=H).status_code == 200
    con = sqlite3.connect(ajustes.base_datos)
    for tabla in ("usuarios", "sesiones", "consentimientos", "credenciales"):
        assert con.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0] == 0
    assert cliente.post("/cuenta/entrar", json={"alias": "ana", "pin": PIN}, headers=H).status_code == 401


def test_opciones_de_passkey_exigen_verificacion_y_clave_residente(cliente):
    _registrar(cliente)
    r = cliente.post("/cuenta/passkeys/opciones", headers=H).json()
    opciones = r["opciones"]
    assert opciones["rp"]["id"] == ajustes.rp_id
    assert opciones["authenticatorSelection"]["residentKey"] == "required"
    assert opciones["authenticatorSelection"]["userVerification"] == "required"
    assert r["reto_id"]


def test_reto_de_passkey_es_de_un_solo_uso(cliente):
    reto_id = cliente.post("/cuenta/passkey/opciones-entrada", headers=H).json()["reto_id"]
    falsa = {"id": "abc", "rawId": "abc", "type": "public-key", "response": {}}
    primero = cliente.post("/cuenta/passkey/entrar", json={"reto_id": reto_id, "credencial": falsa}, headers=H)
    segundo = cliente.post("/cuenta/passkey/entrar", json={"reto_id": reto_id, "credencial": falsa}, headers=H)
    assert primero.status_code == 401
    assert segundo.status_code == 400


def test_reto_de_registro_no_sirve_a_otro_usuario(cliente):
    _registrar(cliente)
    reto_id = cliente.post("/cuenta/passkeys/opciones", headers=H).json()["reto_id"]
    beto = TestClient(app)
    _registrar(beto, alias="beto")
    r = beto.post("/cuenta/passkeys", json={"reto_id": reto_id, "credencial": {"id": "x"}}, headers=H)
    assert r.status_code == 400


def test_logs_sin_alias_ni_pin(cliente, caplog):
    with caplog.at_level(logging.INFO, logger="centinela"):
        _registrar(cliente, alias="secreto")
        cliente.post("/cuenta/entrar", json={"alias": "secreto", "pin": "000001"}, headers=H)
    texto = caplog.text
    assert "secreto" not in texto and PIN not in texto and "000001" not in texto
