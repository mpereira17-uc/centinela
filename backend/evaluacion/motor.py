"""Pasa un guion por las estrategias de alerta, turno a turno, como en la llamada simulada."""
from dataclasses import dataclass, field

from app.config import ajustes
from app.estrategias import Acumulacion, PorFragmento
from app.senales import Nivel

from .guiones import Guion

# Velocidad de habla para estimar tiempos cuando no hay audio (palabras por segundo)
PALABRAS_POR_SEGUNDO = 2.5
PAUSA_ENTRE_TURNOS = 0.6


@dataclass
class Tramo:
    """Un turno de quien llama, con su texto (del guion o transcrito) y sus tiempos en la llamada."""
    indice: int
    texto: str
    inicio: float
    fin: float


@dataclass
class Resultado:
    estrategia: str
    alerta: bool
    indice_alerta: int | None = None
    fin_alerta: float | None = None
    niveles: list[str] = field(default_factory=list)


def estrategias_reglas():
    nivel = Nivel[ajustes.nivel_alerta.upper()]
    return [PorFragmento(nivel), Acumulacion(nivel, ajustes.limite_contexto)]


def estrategias_todas():
    """Reglas, y además el clasificador solo y la híbrida si hay un modelo entrenado."""
    from app.clasificador import Clasificador, Hibrida, cargar

    nivel = Nivel[ajustes.nivel_alerta.upper()]
    modelo = cargar()
    extra = [Clasificador(nivel, modelo), Hibrida(nivel, ajustes.limite_contexto, modelo)] if modelo else []
    return [*estrategias_reglas(), *extra]


def tiempos_estimados(guion: Guion) -> list[tuple[float, float]]:
    """Inicio y fin de cada turno si se leyera en voz alta a un ritmo normal."""
    t, tiempos = 0.0, []
    for turno in guion.turnos:
        duracion = max(1.0, len(turno.texto.split()) / PALABRAS_POR_SEGUNDO)
        tiempos.append((t, t + duracion))
        t += duracion + PAUSA_ENTRE_TURNOS
    return tiempos


def tramos_de_texto(guion: Guion) -> list[Tramo]:
    tiempos = tiempos_estimados(guion)
    return [
        Tramo(i, t.texto, *tiempos[i]) for i, t in enumerate(guion.turnos) if t.hablante == "llamante"
    ]


def correr(tramos: list[Tramo], estrategias) -> list[Resultado]:
    resultados = []
    for e in estrategias:
        r = Resultado(estrategia=e.nombre, alerta=False)
        previos: list[str] = []
        for tramo in tramos:
            d = e.decidir(previos, tramo.texto) if tramo.texto.strip() else None
            previos.append(tramo.texto)
            r.niveles.append(d.nivel if d else "bajo")
            if d and d.alerta and not r.alerta:
                r.alerta, r.indice_alerta, r.fin_alerta = True, tramo.indice, tramo.fin
        resultados.append(r)
    return resultados
