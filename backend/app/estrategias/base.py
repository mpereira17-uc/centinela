import re
import unicodedata
from abc import ABC, abstractmethod

from ..modelos import Decision

# Reglas de referencia: señales de riesgo provisionales. Se reemplazarán o
# complementarán con el clasificador entrenado (scikit-learn / BETO).
SENALES: dict[str, str] = {
    "pide_codigo": r"\b(codigo|clave|contrasena|token|pin)\b",
    "pide_transferencia": r"\b(transfier\w*|consign\w*|nequi|daviplata|gir\w*)\b",
    "urgencia": r"\b(urgente|ya mismo|de inmediato|ahora mismo|rapido)\b",
    "suplanta_entidad": r"\b(banco|fiscalia|policia|dian|soporte tecnico)\b",
    "amenaza": r"\b(captur\w*|embarg\w*|bloque\w*|demanda\w*)\b",
    "secreto": r"\b(no le diga|no cuelgue|no comente|confidencial)\b",
}


def normalizar(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return sin_tildes.lower()


def detectar_senales(texto: str) -> list[str]:
    limpio = normalizar(texto)
    return [nombre for nombre, patron in SENALES.items() if re.search(patron, limpio)]


class Estrategia(ABC):
    nombre: str

    def __init__(self, umbral: float):
        self.umbral = umbral

    @abstractmethod
    def decidir(self, historial: list[str], texto: str) -> Decision:
        """Decide sobre el fragmento nuevo; historial son los textos previos."""
