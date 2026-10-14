from ..modelos import Decision
from .base import Estrategia, detectar_senales


class Acumulacion(Estrategia):
    """Acumula indicios de las últimas intervenciones antes de decidir."""

    nombre = "acumulacion"

    def __init__(self, umbral: float, limite_contexto: int):
        super().__init__(umbral)
        self.limite_contexto = limite_contexto

    def decidir(self, historial: list[str], texto: str) -> Decision:
        ventana = historial[-(self.limite_contexto - 1):] if self.limite_contexto > 1 else []
        indicios: list[str] = []
        for t in [*ventana, texto]:
            for s in detectar_senales(t):
                if s not in indicios:
                    indicios.append(s)
        # Exige más señales que la estrategia por fragmento, pero las suma en el tiempo
        puntaje = min(1.0, len(indicios) / 3)
        return Decision(
            estrategia=self.nombre,
            puntaje=round(puntaje, 3),
            alerta=puntaje >= self.umbral,
            indicios=indicios,
        )
