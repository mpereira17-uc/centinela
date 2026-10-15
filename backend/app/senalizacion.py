"""Señalización para la llamada simulada por WebRTC entre dos navegadores.

El servidor solo presenta a los dos participantes y reenvía sus mensajes de
conexión (oferta, respuesta y candidatos). El audio viaja directo entre los
navegadores y nunca pasa por aquí. Tampoco se guarda nada: las salas viven en
memoria y desaparecen al colgar.
"""
import asyncio
import json
import logging
import secrets
import time
from dataclasses import dataclass, field
from typing import Literal
from urllib.parse import urlparse

from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from .config import ajustes

log = logging.getLogger("centinela")

ROLES = ("llama", "recibe")
Rol = Literal["llama", "recibe"]
ALFABETO = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"  # sin 0/O ni 1/I/L para dictarlo sin errores
MAX_SALAS = 100
VIDA_SALA = 2 * 3600
MAX_MENSAJE = 64 * 1024
MAX_MENSAJES_POR_MINUTO = 600
TIPOS_REENVIADOS = {"oferta", "respuesta", "candidato", "texto", "colgar"}


@dataclass
class Sala:
    codigo: str
    creada: float = field(default_factory=time.time)
    participantes: dict[str, WebSocket] = field(default_factory=dict)


salas: dict[str, Sala] = {}
_lock = asyncio.Lock()


def _limpiar():
    vencidas = [c for c, s in salas.items() if time.time() - s.creada > VIDA_SALA]
    for c in vencidas:
        del salas[c]


def _codigo() -> str:
    while True:
        codigo = "".join(secrets.choice(ALFABETO) for _ in range(6))
        if codigo not in salas:
            return codigo


def _normalizar(codigo: str) -> str:
    return codigo.strip().upper().replace("-", "").replace(" ", "")[:12]


router = APIRouter(tags=["llamada simulada"])


@router.post("/salas", status_code=201)
async def crear_sala():
    async with _lock:
        _limpiar()
        if len(salas) >= MAX_SALAS:
            raise HTTPException(status_code=429, detail="Hay demasiadas llamadas de prueba abiertas. Intenta más tarde.")
        sala = Sala(_codigo())
        salas[sala.codigo] = sala
    log.info("sala creada")
    return {"codigo": sala.codigo}


class EstadoSala(BaseModel):
    codigo: str
    roles_libres: list[Rol]


@router.get("/salas/{codigo}", response_model=EstadoSala)
def ver_sala(codigo: str):
    sala = salas.get(_normalizar(codigo))
    if sala is None:
        raise HTTPException(status_code=404, detail="No existe una llamada con ese código. Revísalo o crea una nueva.")
    return {"codigo": sala.codigo, "roles_libres": [r for r in ROLES if r not in sala.participantes]}


def _mismo_origen(ws: WebSocket) -> bool:
    """Evita que otra página abra la conexión a nombre del usuario (secuestro de WebSocket)."""
    origen = ws.headers.get("origin")
    if origen is None:  # clientes que no son navegadores, como las pruebas
        return True
    # Detrás del túnel de la sustentación el Host puede llegar cambiado; se acepta también el origen configurado
    return urlparse(origen).netloc in (ws.headers.get("host"), urlparse(ajustes.origen).netloc)


async def _enviar(ws: WebSocket | None, mensaje: dict):
    if ws is None:
        return
    try:
        await ws.send_text(json.dumps(mensaje))
    except Exception:
        pass


@router.websocket("/salas/{codigo}/ws")
async def conectar(ws: WebSocket, codigo: str, rol: str):
    if not _mismo_origen(ws) or rol not in ROLES:
        await ws.close(code=4403)
        return
    sala = salas.get(_normalizar(codigo))
    if sala is None:
        await ws.close(code=4404)
        return
    await ws.accept()

    # El primer mensaje debe confirmar que ambas personas saben que la llamada se analiza
    try:
        primero = json.loads(await asyncio.wait_for(ws.receive_text(), timeout=30))
    except Exception:
        await ws.close(code=4400)
        return
    if primero.get("tipo") != "unirse" or primero.get("consentimiento") is not True:
        await ws.close(code=4401)
        return

    async with _lock:
        if rol in sala.participantes or salas.get(sala.codigo) is not sala:
            await ws.close(code=4409)
            return
        sala.participantes[rol] = ws
        completos = len(sala.participantes) == 2
    otro = "recibe" if rol == "llama" else "llama"
    await _enviar(ws, {"tipo": "unido", "rol": rol})
    if completos:
        # Quien llama crea la oferta; quien recibe crea la conversación que se analiza
        for r in ROLES:
            await _enviar(sala.participantes.get(r), {"tipo": "listos"})
    log.info("sala participante=%s completos=%s", rol, completos)

    marcas: list[float] = []
    try:
        while True:
            texto = await ws.receive_text()
            ahora = time.monotonic()
            marcas = [m for m in marcas if ahora - m < 60] + [ahora]
            if len(texto) > MAX_MENSAJE or len(marcas) > MAX_MENSAJES_POR_MINUTO:
                await ws.close(code=4413)
                break
            try:
                mensaje = json.loads(texto)
            except ValueError:
                continue
            if not isinstance(mensaje, dict) or mensaje.get("tipo") not in TIPOS_REENVIADOS:
                continue
            await _enviar(sala.participantes.get(otro), mensaje)
            if mensaje["tipo"] == "colgar":
                break
    except WebSocketDisconnect:
        pass
    finally:
        async with _lock:
            if sala.participantes.get(rol) is ws:
                del sala.participantes[rol]
            restante = sala.participantes.get(otro)
            if not sala.participantes:
                salas.pop(sala.codigo, None)
        await _enviar(restante, {"tipo": "colgo"})
        log.info("sala participante=%s salio", rol)
