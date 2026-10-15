"""Revisión de mensajes (SMS, WhatsApp, correo) y de sus enlaces, sin abrirlos."""
import pytest
from fastapi.testclient import TestClient

from app import enlaces, mensajes
from app.main import app


@pytest.fixture(autouse=True)
def sin_limite():
    mensajes.limite_mensajes.reiniciar()


def _ids(texto):
    return [s["id"] for s in mensajes.analizar(texto)["senales"]]


@pytest.mark.parametrize("enlace,marca", [
    ("bancolombia-seguridad.xyz/clave", "bancolombia"),
    ("https://www.d4vivienda.co/login", "davivienda"),
    ("http://nequi.validar-cuenta.com", "nequi"),
    ("dian-devoluciones.online", "dian"),
    ("https://servientrega-paquetes.info/pago", "servientrega"),
])
def test_un_enlace_que_imita_una_marca_se_marca(enlace, marca):
    r = enlaces.revisar(enlace)
    assert r.imita == marca and r.suplanta


@pytest.mark.parametrize("enlace", [
    "https://www.bancolombia.com/personas", "https://davivienda.com", "https://www.dian.gov.co/tramites",
    "https://transaccional.bancolombia.com", "https://www.mintic.gov.co",
])
def test_los_dominios_oficiales_no_se_marcan(enlace):
    r = enlaces.revisar(enlace)
    assert r.oficial and not r.suplanta and not r.hallazgos


@pytest.mark.parametrize("enlace,pista", [
    ("bit.ly/3xYz", "acortado"),
    ("http://192.168.1.10/pago", "numérica"),
    ("https://xn--bncolombia-9db.com", "otros alfabetos"),
    ("https://www.google.com@estafa.com/login", "@"),
    ("premios-colombia.click", ".click"),
])
def test_enlaces_que_esconden_a_donde_llevan(enlace, pista):
    assert any(pista in h for h in enlaces.revisar(enlace).hallazgos)


def test_extrae_varios_enlaces_sin_repetir_y_con_tope():
    texto = "Mire bit.ly/a y https://x.com/b. Otra vez bit.ly/a " + " ".join(f"s{i}.xyz" for i in range(10))
    lista = enlaces.extraer(texto)
    assert lista[:2] == ["bit.ly/a", "https://x.com/b"] and len(lista) == enlaces.MAX_ENLACES


def test_smishing_tipico_es_alto_o_critico():
    r = mensajes.analizar("Bancolombia le informa: su cuenta fue bloqueada. Ingrese a bancolombia-seguridad.xyz para activarla")
    assert r["nivel"] in ("alto", "critico")
    assert {"enlace_suplanta", "pide_entrar_enlace"} <= set(_ids("Ingrese a bancolombia-seguridad.xyz para activarla"))
    assert r["enlaces"][0]["imita"] == "bancolombia"


def test_paquete_retenido_con_enlace_acortado():
    assert mensajes.analizar("Su paquete está retenido, pague el envío aquí: bit.ly/3xYz")["nivel"] == "alto"


@pytest.mark.parametrize("texto", [
    "Nequi: recibiste 50.000 de Ana. Revisa en la app.",
    "Bancolombia: Tu clave dinámica es 123456. No la compartas con nadie.",
    "Te comparto el link de la reunión: meet.google.com/abc-defg-hij",
    "Hola ma, mira este video https://www.youtube.com/watch?v=abc",
])
def test_mensajes_normales_no_son_alto(texto):
    assert mensajes.analizar(texto)["nivel"] in ("bajo", "moderado")


def test_pedir_reenviar_el_codigo_si_es_riesgo():
    assert "pide_codigo" in _ids("Su clave es 4455. Envíela a este número para activar su cuenta")


def test_la_api_responde_y_explica_su_limite():
    c = TestClient(app)
    r = c.post("/mensajes/analizar", json={"texto": "Reclame su premio en premios-colombia.click"})
    assert r.status_code == 200
    datos = r.json()
    assert "no abre los enlaces" in datos["limite"]
    assert datos["enlaces"][0]["dominio"] == "premios-colombia.click"
    assert c.post("/mensajes/analizar", json={"texto": "x" * 2001}).status_code == 422
    assert c.post("/mensajes/analizar", json={"texto": ""}).status_code == 422
