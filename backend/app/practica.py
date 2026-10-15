"""Modo práctica: llamadas de mentira para aprender a reconocer estafas.

Toma llamadas de la base de guiones (las de prueba y las regionales, que no entrenan
el modelo) y explica en cada una qué la delataba. Sirve para personas mayores y para
probar la app con usuarios del piloto. No guarda nada: el puntaje queda en el navegador.
"""
import random

from fastapi import APIRouter, Depends, Query

from evaluacion import guiones

from .cuentas import LimitePorCliente
from .senales import Tipo, detectar

router = APIRouter(tags=["practica"])
limite_practica = LimitePorCliente(maximo=30, ventana=60)
PARTICIONES = ("sintetica_prueba", "regional")
CONSEJO_LEGITIMA = "No pidió códigos, claves ni plata, y no te apuró. Aun así, si dudas, cuelga y llama tú por el canal oficial."


def _pistas(g) -> list[str]:
    # Lo que delata la estafa: primero lo que piden, luego la presión y el contexto
    orden = {Tipo.SOLICITUD: 0, Tipo.PRESION: 1, Tipo.CONTEXTO: 2}
    vistas = {}
    for t in g.turnos:
        if t.hablante == "llamante":
            for s in detectar(t.texto):
                vistas.setdefault(s.id, s)
    return [s.motivo[0].upper() + s.motivo[1:] for s in sorted(vistas.values(), key=lambda s: orden[s.tipo])][:3]


def _ronda(g) -> dict:
    pistas = _pistas(g) if g.es_riesgo else []
    return {
        "id": g.id,
        "region": g.region,
        "etiqueta": g.etiqueta,
        "turnos": [{"hablante": t.hablante, "texto": t.texto} for t in g.turnos],
        "turno_riesgo": g.turno_riesgo,
        "pistas": pistas,
        # La frase donde está la trampa, para mostrarla resaltada al final
        "frase_clave": g.turnos[g.turno_riesgo].texto if g.es_riesgo else None,
        "explicacion": (g.descripcion + ".") if g.es_riesgo else CONSEJO_LEGITIMA,
    }


@router.get("/practica/rondas", dependencies=[Depends(limite_practica)])
def rondas(cantidad: int = Query(5, ge=1, le=10), semilla: int | None = Query(None, ge=0)):
    base = [g for g in guiones.cargar() if g.particion in PARTICIONES]
    azar = random.Random(semilla)
    riesgo = [g for g in base if g.es_riesgo]
    legit = [g for g in base if not g.es_riesgo]
    # Mitad y mitad (con una de más al azar), para que adivinar siempre "estafa" no gane
    n_riesgo = cantidad // 2 + (azar.random() < 0.5 if cantidad % 2 else 0)
    elegidas = azar.sample(riesgo, n_riesgo) + azar.sample(legit, cantidad - n_riesgo)
    azar.shuffle(elegidas)
    return [_ronda(g) for g in elegidas]
