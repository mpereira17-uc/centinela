"""Señalización para la llamada simulada por WebRTC entre dos navegadores.

El servidor solo presenta a los dos participantes y reenvía sus mensajes de
conexión (oferta, respuesta y candidatos). El audio viaja directo entre los
navegadores y nunca pasa por aquí. Tampoco se guarda nada: las salas viven en
memoria y desaparecen al colgar.

Si la conexión con el servidor se cae sin colgar (el túnel corta, el celular cambia
de red), la llamada no termina: quien se cayó tiene unos segundos para volver con la
llave que recibió al entrar, y mientras tanto la voz sigue directo entre los celulares.
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
TIPOS_REENVIADOS = {"oferta", "respuesta", "candidato", "texto", "colgar", "reiniciar"}
# Segundos que se guarda el lugar de quien perdió la conexión sin colgar
GRACIA = 45
# Cierres del navegador que significan que la persona se fue a propósito
CIERRES_VOLUNTARIOS = {1000, 1001}


@dataclass
class Sala:
    codigo: str
    creada: float = field(default_factory=time.time)
    participantes: dict[str, WebSocket] = field(default_factory=dict)
    # Llave de cada papel tomado, para volver tras un corte sin que otra persona ocupe el lugar
    llaves: dict[str, str] = field(default_factory=dict)
    # Hasta cuándo se guarda el lugar de quien se cayó
    ausentes: dict[str, float] = field(default_factory=dict)
    usada: bool = False
    conectada: bool = False

    def vencer_ausentes(self):
        for rol, hasta in list(self.ausentes.items()):
            if time.time() > hasta:
                del self.ausentes[rol]
                self.llaves.pop(rol, None)

    def abandonada(self) -> bool:
        return self.usada and not self.participantes and not self.ausentes


salas: dict[str, Sala] = {}
_lock = asyncio.Lock()


def _limpiar():
    for s in salas.values():
        s.vencer_ausentes()
    vencidas = [c for c, s in salas.items() if time.time() - s.creada > VIDA_SALA or s.abandonada()]
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
    sala.vencer_ausentes()
    # El lugar de quien se cayó hace un momento sigue siendo suyo
    return {"codigo": sala.codigo, "roles_libres": [r for r in ROLES if r not in sala.llaves]}


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
    if not isinstance(primero, dict) or primero.get("tipo") != "unirse" or primero.get("consentimiento") is not True:
        await ws.close(code=4401)
        return
    llave = primero.get("llave")

    otro = "recibe" if rol == "llama" else "llama"
    reemplazada = None
    async with _lock:
        sala.vencer_ausentes()
        if salas.get(sala.codigo) is not sala:
            await ws.close(code=4404)
            return
        if llave is not None:
            # Vuelve quien se cayó: su llave debe coincidir y su lugar seguir guardado
            guardada = sala.llaves.get(rol)
            if not isinstance(llave, str) or guardada is None or not secrets.compare_digest(llave, guardada):
                await ws.close(code=4410)
                return
            # Si el servidor aún no notó el corte, la conexión vieja se reemplaza
            reemplazada = sala.participantes.get(rol)
            sala.ausentes.pop(rol, None)
        elif rol in sala.llaves:
            await ws.close(code=4409)
            return
        else:
            llave = secrets.token_urlsafe(16)
            sala.llaves[rol] = llave
        sala.participantes[rol] = ws
        sala.usada = True
        completos = len(sala.participantes) == 2
        primera_vez = completos and not sala.conectada
        if primera_vez:
            sala.conectada = True
        otro_ausente = otro in sala.ausentes
    if reemplazada is not None:
        try:
            await reemplazada.close(code=4000)
        except Exception:
            pass

    volvio = primero.get("llave") is not None
    await _enviar(ws, {"tipo": "unido", "rol": rol, "llave": llave, "reconexion": volvio})
    if primera_vez:
        # Quien llama crea la oferta; quien recibe crea la conversación que se analiza
        for r in ROLES:
            await _enviar(sala.participantes.get(r), {"tipo": "listos"})
    elif volvio and completos:
        await _enviar(sala.participantes.get(otro), {"tipo": "volvio"})
    if otro_ausente:
        await _enviar(ws, {"tipo": "reconectando", "segundos": GRACIA})
    log.info("sala participante=%s completos=%s reconexion=%s", rol, completos, volvio)

    marcas: list[float] = []
    se_fue = False
    try:
        while True:
            texto = await ws.receive_text()
            ahora = time.monotonic()
            marcas = [m for m in marcas if ahora - m < 60] + [ahora]
            if len(texto) > MAX_MENSAJE or len(marcas) > MAX_MENSAJES_POR_MINUTO:
                se_fue = True
                await ws.close(code=4413)
                break
            try:
                mensaje = json.loads(texto)
            except ValueError:
                continue
            if not isinstance(mensaje, dict):
                continue
            if mensaje.get("tipo") == "ping":
                # Mantiene viva la conexión: el túnel corta las que pasan un rato en silencio
                await _enviar(ws, {"tipo": "pong"})
                continue
            if mensaje.get("tipo") not in TIPOS_REENVIADOS:
                continue
            await _enviar(sala.participantes.get(otro), mensaje)
            if mensaje["tipo"] == "colgar":
                se_fue = True
                break
    except WebSocketDisconnect as e:
        se_fue = e.code in CIERRES_VOLUNTARIOS
    except Exception:
        pass
    finally:
        async with _lock:
            sigue = sala.participantes.get(rol) is ws
            if sigue:
                del sala.participantes[rol]
                if se_fue:
                    sala.llaves.pop(rol, None)
                    sala.ausentes.pop(rol, None)
                else:
                    sala.ausentes[rol] = time.time() + GRACIA
            restante = sala.participantes.get(otro)
            if sala.abandonada():
                salas.pop(sala.codigo, None)
        if sigue:
            await _enviar(restante, {"tipo": "colgo"} if se_fue else {"tipo": "reconectando", "segundos": GRACIA})
        log.info("sala participante=%s salio=%s", rol, "colgo" if se_fue else ("corte" if sigue else "reemplazada"))
