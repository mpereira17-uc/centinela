from collections.abc import Sequence

from ..modelos import Decision
from ..senales import Nivel, Senal, detectar
from .base import Estrategia


class Acumulacion(Estrategia):
    """Acumula indicios de las últimas intervenciones antes de decidir."""

    nombre = "acumulacion"

    def __init__(self, nivel_alerta: Nivel, limite_contexto: int):
        super().__init__(nivel_alerta)
        self.limite_contexto = limite_contexto

    def decidir(self, historial: list[str], texto: str, externas: Sequence[Senal] = ()) -> Decision:
        ventana = historial[-(self.limite_contexto - 1):] if self.limite_contexto > 1 else []
        senales = []
        for t in [*ventana, texto]:
            for s in detectar(t):
                if s not in senales:
                    senales.append(s)
        return self._decision(senales, externas)
