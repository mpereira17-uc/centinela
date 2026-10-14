import pytest
from fastapi.testclient import TestClient

from app import asistente, main, voz
from app.transcripcion import whisper
from app.transcripcion.whisper import Segmento

cliente = TestClient(main.app)


@pytest.mark.parametrize(
    "frase, intencion",
    [
        ("Analiza esta llamada", "analizar_llamada"),
        ("¿Esta llamada parece una estafa?", "parece_estafa"),
        ("Explícame la alerta", "explicar_alerta"),
        ("Activa mi protección", "activar_proteccion"),
        ("Quiero reportar este número", "reportar_numero"),
        ("Ayúdame a verificar la identidad de esta persona", "verificar_identidad"),
        ("¿Qué puedes hacer?", "ayuda"),
        ("Pon música", "desconocido"),
    ],
)
def test_los_comandos_de_la_especificacion_se_reconocen(frase, intencion):
    assert asistente.interpretar(frase) == intencion


@pytest.mark.parametrize(
    "frase",
    [
        "Desactiva la protección",
        "Borra mis datos",
        "Cambia mi PIN",
        "Transfiere cien mil pesos",
        "Comparte mi clave con el banco",
    ],
)
def test_la_voz_nunca_ejecuta_acciones_sensibles(frase):
    r = asistente.responder(frase, None, "acumulacion")
    assert r.intencion == "accion_sensible"
    assert r.requiere_confirmacion is True
    assert "no lo hago por voz" in r.texto


def _llamada_con(texto):
    llamada_id = cliente.post("/llamadas").json()["id"]
    cliente.post(f"/llamadas/{llamada_id}/fragmentos", json={"texto": texto, "inicio": 0, "fin": 2})
    return llamada_id


def test_parece_estafa_usa_el_nivel_de_la_conversacion():
    llamada_id = _llamada_con("Le hablamos del banco, dígame el código, es urgente")
    r = cliente.post("/asistente", json={"texto": "¿Esto es una estafa?", "llamada_id": llamada_id}).json()
    assert r["intencion"] == "parece_estafa"
    assert r["respuesta"].startswith("El riesgo es crítico.")


def test_explicar_alerta_nombra_las_senales():
    llamada_id = _llamada_con("Dígame el código que le llegó")
    r = cliente.post("/asistente", json={"texto": "Explícame la alerta", "llamada_id": llamada_id}).json()
    assert "código de verificación" in r["respuesta"]
    assert "puedo equivocarme" in r["respuesta"]


def test_sin_conversacion_pide_datos_en_vez_de_inventar():
    r = cliente.post("/asistente", json={"texto": "¿Parece una estafa?"}).json()
    assert "Todavía no hay nada que analizar" in r["respuesta"]


def test_no_promete_lo_que_no_puede_hacer():
    for frase in ("Activa mi protección", "Analiza esta llamada", "Quiero reportar este número"):
        r = cliente.post("/asistente", json={"texto": frase}).json()
        texto = r["respuesta"].lower()
        assert "no puede" in texto or "no puedo" in texto or "no está disponible" in texto


def test_verificar_identidad_advierte_sobre_voces_clonadas():
    r = cliente.post("/asistente", json={"texto": "Ayúdame a verificar la identidad"}).json()
    assert "inteligencia artificial" in r["respuesta"]


def test_consulta_vacia_o_larga_se_rechaza():
    assert cliente.post("/asistente", json={"texto": ""}).status_code == 422
    assert cliente.post("/asistente", json={"texto": "x" * 501}).status_code == 422


def test_comandos_publicos_no_muestran_las_acciones_sensibles():
    ids = [c["id"] for c in cliente.get("/asistente/comandos").json()]
    assert "parece_estafa" in ids and "accion_sensible" not in ids


def test_orden_hablada_se_transcribe_y_se_responde(monkeypatch):
    monkeypatch.setattr(whisper, "transcribir", lambda datos: [Segmento("Explícame la alerta", 0, 1.5)])
    r = cliente.post(
        "/asistente/voz",
        files={"audio": ("orden.webm", b"\x1aE\xdf\xa3" + b"\0" * 50, "audio/webm")},
        data={"consentimiento": "true"},
    )
    assert r.status_code == 200
    assert r.json()["transcripcion"] == "Explícame la alerta"
    assert r.json()["intencion"] == "explicar_alerta"


def test_orden_hablada_sin_consentimiento_se_rechaza(monkeypatch):
    monkeypatch.setattr(whisper, "transcribir", lambda datos: [])
    r = cliente.post(
        "/asistente/voz",
        files={"audio": ("orden.webm", b"abc", "audio/webm")},
        data={"consentimiento": "false"},
    )
    assert r.status_code == 400


def test_voz_sintetica_sin_piper_responde_503(monkeypatch):
    def no_disponible(texto):
        raise voz.VozNoDisponible("No hay una voz de Piper configurada (CENTINELA_VOZ_PIPER).")

    monkeypatch.setattr(voz, "sintetizar", no_disponible)
    r = cliente.post("/voz", json={"texto": "Hola"})
    assert r.status_code == 503


def test_voz_sintetica_devuelve_wav(monkeypatch):
    monkeypatch.setattr(voz, "sintetizar", lambda texto: b"RIFF0000WAVE")
    r = cliente.post("/voz", json={"texto": "Hola"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "audio/wav"
    assert r.headers["cache-control"] == "no-store"
