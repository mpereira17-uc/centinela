from ..modelos import Decision
from .base import Estrategia, detectar_senales


class PorFragmento(Estrategia):
    """Decide mirando solo el fragmento actual."""

    nombre = "por_fragmento"

    def decidir(self, historial: list[str], texto: str) -> Decision:
        indicios = detectar_senales(texto)
        # Con dos señales distintas en el mismo fragmento ya se supera el umbral
        puntaje = min(1.0, len(indicios) / 2)
        return Decision(
            estrategia=self.nombre,
            puntaje=round(puntaje, 3),
            alerta=puntaje >= self.umbral,
            indicios=indicios,
        )
