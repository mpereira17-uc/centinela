"""Transcripción local con faster-whisper en CPU.

El audio llega en memoria, se transcribe y se descarta: nunca se escribe en
disco ni sale del equipo (modelo de amenazas, A9). faster-whisper se importa de
forma perezosa para que el backend arranque aunque no esté instalado.
"""
import io
from dataclasses import dataclass
from functools import lru_cache

from ..config import ajustes


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
    modelo = _modelo()
    try:
        segmentos, _ = modelo.transcribe(io.BytesIO(audio), language="es", vad_filter=True)
        # transcribe() es perezoso: el audio se decodifica al recorrer los segmentos
        return [Segmento(s.text.strip(), s.start, s.end) for s in segmentos if s.text.strip()]
    except Exception as e:
        raise AudioInvalido("No pudimos leer el audio. Prueba con un archivo WAV, MP3, M4A, OGG o WebM.") from e
