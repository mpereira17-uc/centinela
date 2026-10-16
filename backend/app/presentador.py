"""Pantalla del presentador: lo que oye el celular de un jurado, en vivo, en el video beam.

Muestra las tres estrategias que compara la tesis lado a lado (por frase, acumulada e
híbrida) sobre la misma conversación, y en qué frase avisó cada una. Solo existe mientras
la sustentación la activa con una llave (CENTINELA_PRESENTADOR_LLAVE, la pone
sustentacion.py), y solo muestra las llamadas en las que alguien marcó "Mostrar en la
pantalla del presentador". Vive en memoria: no se guarda y se borra al apagar.
"""
import itertools
import secrets
import threading
from collections import deque

from fastapi import APIRouter, Header, HTTPException

from .config import ajustes

MAX_EVENTOS = 500
_eventos: deque = deque(maxlen=MAX_EVENTOS)
_lock = threading.Lock()
_contador = itertools.count(1)
_numeros = itertools.count(1)

router = APIRouter(prefix="/presentador", tags=["pantalla del presentador"])


def activo() -> bool:
    return bool(ajustes.presentador_llave)


def numerar() -> int:
    """Número corto para la pantalla ("Llamada 3"), en vez del identificador de la llamada."""
    return next(_numeros)


def publicar(evento: dict):
    if not activo():
        return
    with _lock:
        _eventos.append({"n": next(_contador), **evento})


def _autorizar(llave: str | None):
    if not activo() or llave is None or not secrets.compare_digest(llave, ajustes.presentador_llave):
        raise HTTPException(status_code=403, detail="Falta la llave de la pantalla del presentador.")


@router.get("/estado")
def estado():
    """Las pantallas preguntan esto para ofrecer la casilla de mostrar la llamada."""
    return {"activo": activo()}


@router.get("/eventos")
def eventos(desde: int = 0, x_presentador: str | None = Header(default=None)):
    _autorizar(x_presentador)
    with _lock:
        nuevos = [e for e in _eventos if e["n"] > desde]
    from .analisis import ESTRATEGIA_VISIBLE, estrategias

    return {"eventos": nuevos, "estrategias": [e.nombre for e in estrategias], "visible": ESTRATEGIA_VISIBLE}


@router.delete("/eventos", status_code=204)
def limpiar(x_presentador: str | None = Header(default=None)):
    _autorizar(x_presentador)
    with _lock:
        _eventos.clear()
