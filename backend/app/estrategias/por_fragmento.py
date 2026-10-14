from ..modelos import Decision
from ..senales import detectar
from .base import Estrategia


class PorFragmento(Estrategia):
    """Decide mirando solo el fragmento actual."""

    nombre = "por_fragmento"

    def decidir(self, historial: list[str], texto: str) -> Decision:
        return self._decision(detectar(texto))
