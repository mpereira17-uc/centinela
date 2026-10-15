from abc import ABC, abstractmethod
from collections.abc import Sequence

from ..modelos import Decision, SenalDetectada
from ..senales import NUMERO_REPORTADO, Nivel, Senal, calcular_nivel, mensaje
from ..voz_clonada import por_contexto


class Estrategia(ABC):
    nombre: str

    def __init__(self, nivel_alerta: Nivel):
        # Nivel mínimo a partir del cual la estrategia emite alerta
        self.nivel_alerta = nivel_alerta

    @abstractmethod
    def decidir(self, historial: list[str], texto: str, externas: Sequence[Senal] = ()) -> Decision:
        """Decide sobre el fragmento nuevo; historial son los textos previos.

        externas son señales que no salen del texto, como la reputación del número.
        """

    def _decision(self, senales: list[Senal], externas: Sequence[Senal] = ()) -> Decision:
        senales = [*senales, *(s for s in externas if s not in senales)]
        # Supuesto familiar que pide algo: la voz se puede clonar (solo sube el nivel)
        senales += por_contexto(senales)
        nivel = calcular_nivel(senales)
        return Decision(
            estrategia=self.nombre,
            nivel=nivel.etiqueta,
            alerta=nivel >= self.nivel_alerta,
            mensaje=mensaje(nivel, senales),
            senales=[SenalDetectada(id=s.id, tipo=s.tipo, descripcion=s.descripcion) for s in senales],
            fuente="contenido_y_reputacion" if NUMERO_REPORTADO in externas else "contenido",
        )
