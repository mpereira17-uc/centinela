"""Clasificador entrenado (TF-IDF + regresión logística) y estrategia híbrida.

El modelo se entrena con scikit-learn (backend/evaluacion/entrenar.py) y se guarda
como JSON: vocabulario, pesos IDF y coeficientes. Aquí se aplica con Python puro,
así que el servidor no necesita scikit-learn ni carga archivos pickle, que pueden
ejecutar código al abrirse (modelo de amenazas, A19).
"""
import json
import logging
import math
import re
from collections import Counter
from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path

from .modelos import Decision
from .senales import Nivel, Senal, Tipo, _p, detectar, normalizar
from .estrategias.base import Estrategia

log = logging.getLogger("centinela")

RUTA_MODELO = Path(__file__).with_name("modelo_clasificador.json")

# Señal que agrega el clasificador cuando una frase se parece a las solicitudes de riesgo del entrenamiento
PATRON_APRENDIDO = Senal(
    "patron_aprendido",
    Tipo.SOLICITUD,
    "La frase se parece a solicitudes de estafa del conjunto de entrenamiento (modelo estadístico, puede equivocarse)",
    "lo que te piden se parece a estafas conocidas",
    _p(r"(?!)"),
)


def caracteristicas(texto: str) -> list[str]:
    """Palabras, pares de palabras y trozos de 3 a 5 letras de cada palabra.

    Los trozos de letras ayudan con variaciones ("consigne", "consígnelo") y errores de transcripción.
    """
    palabras = re.findall(r"[a-z0-9]+", normalizar(texto))
    salida = [f"p:{p}" for p in palabras]
    salida += [f"pp:{a}_{b}" for a, b in zip(palabras, palabras[1:])]
    for p in palabras:
        rodeada = f" {p} "
        for n in (3, 4, 5):
            salida += [f"l:{rodeada[i:i + n]}" for i in range(len(rodeada) - n + 1)]
    return salida


class Modelo:
    def __init__(self, datos: dict):
        self.vocabulario: dict[str, int] = datos["vocabulario"]
        self.idf: list[float] = datos["idf"]
        self.coef: list[float] = datos["coef"]
        self.intercepto: float = datos["intercepto"]
        self.umbral: float = datos["umbral"]
        self.version: str = datos.get("version", "")

    def probabilidad(self, texto: str) -> float:
        """Probabilidad de que la frase sea una solicitud de riesgo, igual que predict_proba de scikit-learn."""
        conteos = Counter(i for f in caracteristicas(texto) if (i := self.vocabulario.get(f)) is not None)
        if not conteos:
            return 1 / (1 + math.exp(-self.intercepto))
        # tf sublineal, idf y normalización L2, como TfidfVectorizer(sublinear_tf=True)
        pesos = {i: (1 + math.log(c)) * self.idf[i] for i, c in conteos.items()}
        norma = math.sqrt(sum(v * v for v in pesos.values()))
        z = self.intercepto + sum(self.coef[i] * v / norma for i, v in pesos.items())
        return 1 / (1 + math.exp(-z))


@lru_cache(maxsize=4)
def cargar(ruta: str = str(RUTA_MODELO)) -> Modelo | None:
    try:
        return Modelo(json.loads(Path(ruta).read_text(encoding="utf-8")))
    except FileNotFoundError:
        return None


class Clasificador(Estrategia):
    """Solo el modelo: avisa si la frase actual supera el umbral. Se usa para comparar en la evaluación."""

    nombre = "clasificador"

    def __init__(self, nivel_alerta: Nivel, modelo: Modelo):
        super().__init__(nivel_alerta)
        self.modelo = modelo

    def decidir(self, historial: list[str], texto: str, externas: Sequence[Senal] = ()) -> Decision:
        senales = [PATRON_APRENDIDO] if self.modelo.probabilidad(texto) >= self.modelo.umbral else []
        return self._decision(senales, externas)


class Hibrida(Estrategia):
    """Acumulación de indicios por reglas más el clasificador sobre las mismas frases recientes.

    El clasificador solo puede sumar la señal patron_aprendido; nunca quita señales de las reglas.
    """

    nombre = "hibrida"

    def __init__(self, nivel_alerta: Nivel, limite_contexto: int, modelo: Modelo):
        super().__init__(nivel_alerta)
        self.limite_contexto = limite_contexto
        self.modelo = modelo

    def decidir(self, historial: list[str], texto: str, externas: Sequence[Senal] = ()) -> Decision:
        ventana = historial[-(self.limite_contexto - 1):] if self.limite_contexto > 1 else []
        senales: list[Senal] = []
        for t in [*ventana, texto]:
            for s in detectar(t):
                if s not in senales:
                    senales.append(s)
        if any(self.modelo.probabilidad(t) >= self.modelo.umbral for t in [*ventana, texto]):
            senales.append(PATRON_APRENDIDO)
        return self._decision(senales, externas)
