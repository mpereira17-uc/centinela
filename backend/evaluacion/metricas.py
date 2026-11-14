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


def percentil(valores: list[float], q: float) -> float | None:
    """Percentil q (0 a 100) con interpolación lineal entre los dos valores vecinos."""
    if not valores:
        return None
    v = sorted(valores)
    pos = (len(v) - 1) * q / 100
    bajo = int(pos)
    alto = min(bajo + 1, len(v) - 1)
    return v[bajo] + (v[alto] - v[bajo]) * (pos - bajo)


def f1(vp: int, fp: int, fn: int) -> float | None:
    """Media armónica de precisión y sensibilidad."""
    return 2 * vp / (2 * vp + fp + fn) if vp + fp + fn else None


def bootstrap_diferencia(grupos: list[list[tuple[bool, bool]]], repeticiones: int = 2000,
                         semilla: int = 7) -> tuple[float, float, float] | None:
    """Diferencia B - A en la proporción de llamadas con aviso y su intervalo del 95 %.

    Cada par es (aviso de A, aviso de B) en la misma llamada completa. Se remuestrean
    llamadas, no fragmentos, porque los turnos de una conversación no son independientes;
    y las llamadas de una misma familia (una plantilla en varias regiones) se sacan juntas,
    porque comparten la forma del engaño.
    """
    import random

    grupos = [g for g in grupos if g]
    if not grupos:
        return None

    def dif(muestra):
        pares = [p for g in muestra for p in g]
        return sum(b - a for a, b in pares) / len(pares)

    k = len(grupos)
    azar = random.Random(semilla)
    difs = sorted(dif([grupos[azar.randrange(k)] for _ in range(k)]) for _ in range(repeticiones))
    return dif(grupos), difs[int(0.025 * repeticiones)], difs[int(0.975 * repeticiones) - 1]
