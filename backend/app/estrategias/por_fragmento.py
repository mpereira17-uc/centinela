from collections.abc import Sequence

from ..modelos import Decision
from ..senales import Senal, detectar
from .base import Estrategia


class PorFragmento(Estrategia):
    """Decide mirando solo el fragmento actual."""

    nombre = "por_fragmento"

    def decidir(self, historial: list[str], texto: str, externas: Sequence[Senal] = ()) -> Decision:
        return self._decision(detectar(texto), externas)
