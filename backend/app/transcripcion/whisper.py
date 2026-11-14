"""Transcripción local con faster-whisper en CPU.

El audio llega en memoria, se transcribe y se descarta: nunca se escribe en
disco ni sale del equipo (modelo de amenazas, A9). faster-whisper se importa de
forma perezosa para que el backend arranque aunque no esté instalado.

Para la sustentación el modelo se puede precargar al arrancar ([precargar]): así la
primera frase no espera a que se lea el modelo del disco y el aviso llega a tiempo.
"""
import io
import logging
import threading
import time
from dataclasses import dataclass
from functools import lru_cache

from ..config import ajustes

log = logging.getLogger("centinela")

# Lo que se sabe de la transcripción, sin nada de lo que se dijo
_estado = {"estado": "sin_cargar", "detalle": "", "ultima_segundos": None}


class TranscripcionNoDisponible(Exception):
    """faster-whisper no está instalado o el modelo no se pudo cargar."""


class AudioInvalido(Exception):
    """El archivo no se pudo decodificar como audio."""


@dataclass
class Segmento:
    texto: str
    inicio: float
    fin: float


@lru_cache(maxsize=1)
def _modelo():
    try:
        from faster_whisper import WhisperModel
    except ImportError as e:
        raise TranscripcionNoDisponible(
            "La transcripción no está instalada. Ejecuta: pip install -r requirements-ml.txt"
        ) from e
    try:
        return WhisperModel(ajustes.modelo_whisper, device="cpu", compute_type="int8")
    except Exception as e:  # descarga fallida, modelo corrupto, sin espacio
        raise TranscripcionNoDisponible(
            f"No se pudo cargar el modelo de transcripción '{ajustes.modelo_whisper}'. "
            "La primera vez necesita internet para descargarlo."
        ) from e


def transcribir(audio: bytes) -> list[Segmento]:
    """Devuelve los segmentos con texto e instantes de inicio y fin en segundos."""
    modelo = _cargar()
    inicio = time.perf_counter()
    try:
        segmentos, _ = modelo.transcribe(
            io.BytesIO(audio), language="es", vad_filter=True, beam_size=ajustes.whisper_haz,
            # Cada trozo es una frase suelta: arrastrar el texto anterior solo agrega repeticiones inventadas
            condition_on_previous_text=False,
        )
        # transcribe() es perezoso: el audio se decodifica al recorrer los segmentos
        resultado = [Segmento(s.text.strip(), s.start, s.end) for s in segmentos if s.text.strip()]
    except Exception as e:
        raise AudioInvalido("No pudimos leer el audio. Prueba con un archivo WAV, MP3, M4A, OGG o WebM.") from e
    _estado["ultima_segundos"] = round(time.perf_counter() - inicio, 2)
    return resultado


def _cargar():
    try:
        modelo = _modelo()
    except TranscripcionNoDisponible as e:
        _estado.update(estado="no_disponible", detalle=str(e))
        raise
    if _estado["estado"] != "lista":
        _estado.update(estado="lista", detalle="")
    return modelo


def precargar():
    """Lee el modelo y hace una transcripción de prueba con un segundo de silencio."""
    _estado.update(estado="cargando", detalle="")
    try:
        import numpy as np

        modelo = _cargar()
        inicio = time.perf_counter()
        list(modelo.transcribe(np.zeros(16000, dtype=np.float32), language="es", beam_size=ajustes.whisper_haz)[0])
        log.info("transcripcion=lista modelo=%s prueba_segundos=%.2f", ajustes.modelo_whisper, time.perf_counter() - inicio)
    except TranscripcionNoDisponible:
        log.warning("transcripcion=no_disponible")
    except Exception as e:  # numpy ausente u otro fallo de la prueba: la transcripción real lo dirá
        log.warning("transcripcion=prueba_fallida error=%s", type(e).__name__)
        if _estado["estado"] == "cargando":
            _estado["estado"] = "sin_cargar"


def precargar_en_segundo_plano():
    threading.Thread(target=precargar, name="precarga-whisper", daemon=True).start()


def estado() -> dict:
    return {"modelo": ajustes.modelo_whisper, **_estado}
