"""Señal experimental de voz clonada.

Dos partes, y ninguna dice jamás que una voz es auténtica:

1. Por contexto (siempre activa): alguien dice ser de la familia o un conocido, o cuenta
   una emergencia familiar, y además pide plata, un código o datos. Es el guion típico de
   la voz clonada. Se suma como presión, así que con la solicitud llega a crítico.
2. Acústica (apagada por defecto): si se instala un modelo ONNX y se indica su ruta en
   CENTINELA_MODELO_VOZ, el audio subido se pasa por él. Solo si el puntaje supera un umbral
   alto se agrega una señal de contexto. Si el modelo no está, falla o da un puntaje bajo,
   no se agrega nada: la ausencia de la señal no significa que la voz sea real.

Las dos solo pueden subir el nivel: agregan señales y calcular_nivel nunca baja al
agregar una señal (modelo de amenazas, A26).
"""
import io
import logging
import os
from functools import lru_cache

from .senales import Senal, Tipo, _p

log = logging.getLogger("centinela.voz")

VOZ_DUDOSA = Senal(
    "voz_dudosa",
    Tipo.PRESION,
    "Dice ser de tu familia o un conocido y pide plata, un código o datos: la voz se puede imitar con inteligencia artificial",
    "alguien que dice ser de tu familia te pide plata o un código",
    _p(r"(?!)"),
)

VOZ_SINTETICA = Senal(
    "voz_sintetica",
    Tipo.CONTEXTO,
    "El audio tiene rasgos de voz generada por computador (señal experimental, puede equivocarse)",
    "la voz podría estar generada por computador",
    _p(r"(?!)"),
)

_FAMILIA = {"finge_conocido", "emergencia_familiar"}
_PIDE = {"pide_transferencia", "pide_codigo", "pide_datos_bancarios"}


def por_contexto(senales) -> list[Senal]:
    """Agrega voz_dudosa si en la conversación hay un supuesto familiar que pide algo."""
    ids = {s.id for s in senales}
    if ids & _FAMILIA and ids & _PIDE and VOZ_DUDOSA.id not in ids:
        return [VOZ_DUDOSA]
    return []


class DetectorAcustico:
    """Envoltura opcional de un modelo ONNX que recibe audio mono a 16 kHz (float32, [1, n])
    y devuelve la probabilidad de que sea voz sintética."""

    FRECUENCIA = 16000
    MAX_SEGUNDOS = 30

    def __init__(self, ruta: str | None = None, umbral: float | None = None):
        self.ruta = ruta if ruta is not None else os.environ.get("CENTINELA_MODELO_VOZ", "")
        # Umbral alto a propósito: una falsa alarma aquí asusta a una familia
        self.umbral = umbral if umbral is not None else float(os.environ.get("CENTINELA_UMBRAL_VOZ", "0.9"))

    @property
    def activo(self) -> bool:
        return bool(self.ruta) and os.path.isfile(self.ruta)

    @lru_cache(maxsize=1)
    def _sesion(self):
        import onnxruntime  # opcional: solo si se activa el detector

        return onnxruntime.InferenceSession(self.ruta, providers=["CPUExecutionProvider"])

    def _decodificar(self, datos: bytes):
        from faster_whisper import decode_audio

        return decode_audio(io.BytesIO(datos), sampling_rate=self.FRECUENCIA)[: self.FRECUENCIA * self.MAX_SEGUNDOS]

    def puntaje(self, datos: bytes) -> float | None:
        """Probabilidad de voz sintética, o None si el detector no está o no pudo decidir."""
        if not self.activo:
            return None
        try:
            import numpy as np

            onda = np.asarray(self._decodificar(datos), dtype=np.float32)[None, :]
            sesion = self._sesion()
            salida = sesion.run(None, {sesion.get_inputs()[0].name: onda})[0]
            return float(np.ravel(salida)[-1])
        except Exception:  # sin dependencias, audio raro o modelo incompatible: no decide
            log.warning("detector de voz no pudo evaluar el audio")
            return None

    def es_sintetica(self, datos: bytes) -> bool:
        p = self.puntaje(datos)
        return p is not None and p >= self.umbral


detector = DetectorAcustico()
