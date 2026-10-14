from abc import ABC, abstractmethod

from ..modelos import Decision, SenalDetectada
from ..senales import Nivel, Senal, calcular_nivel, mensaje


class Estrategia(ABC):
    nombre: str

    def __init__(self, nivel_alerta: Nivel):
        # Nivel mínimo a partir del cual la estrategia emite alerta
        self.nivel_alerta = nivel_alerta

    @abstractmethod
    def decidir(self, historial: list[str], texto: str) -> Decision:
        """Decide sobre el fragmento nuevo; historial son los textos previos."""

    def _decision(self, senales: list[Senal]) -> Decision:
        nivel = calcular_nivel(senales)
        return Decision(
            estrategia=self.nombre,
            nivel=nivel.etiqueta,
            alerta=nivel >= self.nivel_alerta,
            mensaje=mensaje(nivel, senales),
            senales=[SenalDetectada(id=s.id, tipo=s.tipo, descripcion=s.descripcion) for s in senales],
        )
