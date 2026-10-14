import pytest
from fastapi.testclient import TestClient

from app import main
from app.transcripcion import whisper
from app.transcripcion.whisper import Segmento

cliente = TestClient(main.app)

# Bytes cualesquiera: en estas pruebas el transcriptor se reemplaza, así que no se decodifican
AUDIO = b"RIFF....WAVEfmt " + b"\0" * 100


@pytest.fixture
def transcriptor_falso(monkeypatch):
    """Sustituye faster-whisper por segmentos fijos, para probar la API sin el modelo."""
    recibido = {}

    def falso(datos):
        recibido["tipo"] = type(datos)
        return [
            Segmento("Le hablamos del banco.", 0.0, 2.0),
            Segmento("Dígame el código que le llegó, es urgente.", 2.0, 5.0),
        ]

    monkeypatch.setattr(whisper, "transcribir", falso)
    return recibido


def _llamada():
    return cliente.post("/llamadas").json()["id"]


def _subir(llamada_id, consentimiento="true", contenido=AUDIO, tipo="audio/wav"):
    return cliente.post(
        f"/llamadas/{llamada_id}/audio",
        files={"audio": ("prueba.wav", contenido, tipo)},
        data={"consentimiento": consentimiento},
    )


def test_cada_segmento_se_analiza_como_un_fragmento(transcriptor_falso):
    r = _subir(_llamada())
    assert r.status_code == 200
    cuerpo = r.json()
    assert [x["fragmento"]["texto"] for x in cuerpo["resultados"]] == [
        "Le hablamos del banco.",
        "Dígame el código que le llegó, es urgente.",
    ]
    assert cuerpo["resultados"][-1]["decision_visible"]["nivel"] == "critico"
    assert cuerpo["mostrar_aviso"] is True


def test_el_audio_se_pasa_en_memoria_y_no_como_archivo(transcriptor_falso):
    _subir(_llamada())
    assert transcriptor_falso["tipo"] is bytes


def test_los_tiempos_continuan_despues_de_lo_escrito(transcriptor_falso):
    llamada_id = _llamada()
    cliente.post(f"/llamadas/{llamada_id}/fragmentos", json={"texto": "Hola", "inicio": 0, "fin": 10})
    r = _subir(llamada_id)
    primero = r.json()["resultados"][0]["fragmento"]
    assert (primero["inicio"], primero["fin"]) == (10.0, 12.0)


def test_sin_consentimiento_no_se_transcribe(transcriptor_falso):
    r = _subir(_llamada(), consentimiento="false")
    assert r.status_code == 400
    assert "tipo" not in transcriptor_falso


def test_rechaza_archivos_que_no_son_audio(transcriptor_falso):
    assert _subir(_llamada(), tipo="text/html").status_code == 415


def test_rechaza_audio_vacio(transcriptor_falso):
    assert _subir(_llamada(), contenido=b"").status_code == 400


def test_rechaza_audio_de_mas_de_10_mb(transcriptor_falso):
    grande = b"\0" * (main.MAX_AUDIO_BYTES + 1)
    assert _subir(_llamada(), contenido=grande).status_code == 413


def test_sin_faster_whisper_responde_503_con_instrucciones(monkeypatch):
    def no_instalado(datos):
        raise whisper.TranscripcionNoDisponible("La transcripción no está instalada. Ejecuta: pip install -r requirements-ml.txt")

    monkeypatch.setattr(whisper, "transcribir", no_instalado)
    r = _subir(_llamada())
    assert r.status_code == 503
    assert "requirements-ml.txt" in r.json()["detail"]


def test_audio_que_no_se_puede_leer_responde_422(monkeypatch):
    def invalido(datos):
        raise whisper.AudioInvalido("No pudimos leer el audio.")

    monkeypatch.setattr(whisper, "transcribir", invalido)
    assert _subir(_llamada()).status_code == 422


def test_el_modulo_real_no_carga_el_modelo_al_importar():
    # El backend debe arrancar aunque faster-whisper no esté instalado
    assert whisper._modelo.cache_info().currsize == 0
