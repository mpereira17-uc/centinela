"""Chequeo rápido para cualquier llamada telefónica, sin audio.

Android no deja que una app oiga una llamada del sistema, así que durante una llamada normal
la persona responde tres preguntas con un toque. Cada respuesta "sí" equivale a una señal del
catálogo y el nivel sale de las mismas reglas que usa el motor (calcular_nivel), para que el
aviso diga lo mismo que diría si Centinela oyera la conversación. No se guarda nada.
"""
from fastapi import APIRouter
from pydantic import BaseModel

from .modelos import Decision, SenalDetectada
from .senales import CATALOGO, Nivel, Senal, Tipo, _p, calcular_nivel, mensaje

router = APIRouter(tags=["chequeo"])

_POR_ID = {s.id: s for s in CATALOGO}

# Una sola señal de presión para la tercera pregunta: prisa, amenaza o secreto suelen ir juntos
PRESION_DECLARADA = Senal(
    "presion_declarada",
    Tipo.PRESION,
    "Quien llama apura, amenaza o pide no contarle a nadie",
    "te están apurando o pidiendo que no le cuentes a nadie",
    _p(r"(?!)"),
)
PLATA_DECLARADA = Senal(
    "plata_declarada",
    Tipo.SOLICITUD,
    "Quien llama pide plata, ir al cajero o instalar una aplicación",
    "te piden plata, ir al cajero o instalar algo",
    _p(r"(?!)"),
)


class Respuestas(BaseModel):
    codigo: bool = False  # ¿Te pidieron un código, clave o datos de la tarjeta?
    plata: bool = False  # ¿Te piden plata, ir al cajero o instalar una app?
    presion: bool = False  # ¿Te apuran, amenazan o piden no contarle a nadie?


class ResultadoChequeo(BaseModel):
    decision: Decision
    mostrar_aviso: bool


def evaluar(r: Respuestas) -> Decision:
    senales: list[Senal] = []
    if r.codigo:
        senales.append(_POR_ID["pide_codigo"])
    if r.plata:
        senales.append(PLATA_DECLARADA)
    if r.presion:
        senales.append(PRESION_DECLARADA)
    nivel = calcular_nivel(senales)
    return Decision(
        estrategia="chequeo",
        nivel=nivel.etiqueta,
        alerta=nivel >= Nivel.ALTO,
        mensaje=mensaje(nivel, senales),
        senales=[SenalDetectada(id=s.id, tipo=s.tipo, descripcion=s.descripcion) for s in senales],
    )


@router.post("/chequeo", response_model=ResultadoChequeo)
def chequeo(respuestas: Respuestas) -> ResultadoChequeo:
    decision = evaluar(respuestas)
    return ResultadoChequeo(decision=decision, mostrar_aviso=decision.alerta)
