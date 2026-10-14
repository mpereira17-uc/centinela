"""Voz sintética local con Piper TTS.

Se importa de forma perezosa. Si Piper o la voz no están instalados, la API
responde 503 y la interfaz usa la voz del navegador.
"""
import io
import wave
from functools import lru_cache

from .config import ajustes


class VozNoDisponible(Exception):
    pass


@lru_cache(maxsize=1)
def _voz():
    if not ajustes.voz_piper:
        raise VozNoDisponible("No hay una voz de Piper configurada (CENTINELA_VOZ_PIPER).")
    try:
        from piper import PiperVoice
    except ImportError as e:
        raise VozNoDisponible("Piper no está instalado. Ejecuta: pip install -r requirements-ml.txt") from e
    try:
        return PiperVoice.load(ajustes.voz_piper)
    except Exception as e:
        raise VozNoDisponible(f"No se pudo cargar la voz {ajustes.voz_piper}.") from e


def sintetizar(texto: str) -> bytes:
    """Devuelve el texto hablado como WAV, sin escribir nada en disco."""
    voz = _voz()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav:
        voz.synthesize_wav(texto, wav)
    return buffer.getvalue()
