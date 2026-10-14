"""Métricas de la evaluación, sin dependencias externas."""
import math
import re
import unicodedata


def normalizar(texto: str) -> list[str]:
    """Palabras en minúscula, sin tildes ni puntuación, para comparar transcripciones."""
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode().lower()
    return re.findall(r"[a-z0-9]+", sin_tildes)


def wer(referencia: str, hipotesis: str) -> tuple[int, int]:
    """Errores de palabra (sustituciones + inserciones + borrados) y palabras de la referencia.

    Se devuelven por separado para sumar todos los turnos antes de dividir.
    """
    ref, hip = normalizar(referencia), normalizar(hipotesis)
    previa = list(range(len(hip) + 1))
    for i, r in enumerate(ref, 1):
        actual = [i] + [0] * len(hip)
        for j, h in enumerate(hip, 1):
            actual[j] = min(previa[j] + 1, actual[j - 1] + 1, previa[j - 1] + (r != h))
        previa = actual
    return previa[-1], len(ref)


def wilson(aciertos: int, total: int, z: float = 1.96) -> tuple[float, float] | None:
    """Intervalo de confianza del 95 % para una proporción; útil con muestras pequeñas."""
    if total == 0:
        return None
    p = aciertos / total
    centro = (p + z * z / (2 * total)) / (1 + z * z / total)
    margen = z * math.sqrt(p * (1 - p) / total + z * z / (4 * total * total)) / (1 + z * z / total)
    return max(0.0, centro - margen), min(1.0, centro + margen)


def mediana(valores: list[float]) -> float | None:
    if not valores:
        return None
    v = sorted(valores)
    medio = len(v) // 2
    return v[medio] if len(v) % 2 else (v[medio - 1] + v[medio]) / 2
