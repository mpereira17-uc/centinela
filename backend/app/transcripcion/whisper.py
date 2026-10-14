"""Transcripción con faster-whisper en CPU.

Se importa de forma perezosa para que el backend arranque aunque no estén
instaladas las dependencias de requirements-ml.txt.
"""
from functools import lru_cache

from ..config import ajustes


@lru_cache(maxsize=1)
def _modelo():
    from faster_whisper import WhisperModel

    return WhisperModel(ajustes.modelo_whisper, device="cpu", compute_type="int8")


def transcribir(ruta_audio: str) -> list[dict]:
    """Devuelve segmentos con texto e instantes de inicio y fin."""
    segmentos, _ = _modelo().transcribe(ruta_audio, language="es", vad_filter=True)
    return [{"texto": s.text.strip(), "inicio": s.start, "fin": s.end} for s in segmentos]
