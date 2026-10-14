"""Reporte comunitario de números.

- Los reportes son seudónimos: nadie más que el autor ve quién reportó (A16).
- El número se guarda como HMAC con una clave local, no en claro; solo se guardan
  sus últimos 4 dígitos para que el autor reconozca sus propios reportes.
- Cada cuenta reporta un número una sola vez y como máximo 10 números por día (A15).
- La reputación es una señal de contexto más; nunca decide sola y "reportado" no
  significa "confirmado" (A15).
"""
import hashlib
import hmac
import logging
import re
import secrets
import time
import uuid
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .cuentas import LimitePorCliente, Sesion, exigir_cabecera, usuario_actual
from .db import conexion

log = logging.getLogger("centinela")

MAX_REPORTES_POR_DIA = 10
# Ventana en la que cuentan los reportes; los números cambian de dueño con el tiempo
VIGENCIA_REPORTE = 180 * 86400
# Personas distintas necesarias para que la reputación pese en el análisis
UMBRAL_SENAL = 2

CATEGORIAS = {
    "suplanta_entidad": "Se hizo pasar por un banco, una empresa o una entidad",
    "premio_falso": "Ofreció un premio, un subsidio o una inversión",
    "extorsion": "Amenazó o extorsionó",
    "familiar_falso": "Se hizo pasar por un familiar o conocido",
    "soporte_falso": "Dijo ser soporte técnico y pidió instalar algo",
    "otro": "Otro intento de estafa",
}
Categoria = Literal["suplanta_entidad", "premio_falso", "extorsion", "familiar_falso", "soporte_falso", "otro"]


class NumeroInvalido(ValueError):
    pass


def normalizar_numero(texto: str) -> str:
    """Devuelve el número en formato internacional sin '+' (por ejemplo 573001234567).

    Los números colombianos de 10 dígitos (celulares 3xx y fijos 60x) reciben el indicativo 57.
    """
    texto = texto.strip()
    internacional = texto.startswith("+") or texto.startswith("00")
    digitos = re.sub(r"\D", "", texto)
    if texto.startswith("00"):
        digitos = digitos[2:]
    if not internacional and len(digitos) == 10 and digitos[0] in "36":
        digitos = "57" + digitos
    if not 7 <= len(digitos) <= 15:
        raise NumeroInvalido("Escribe un número de teléfono válido, por ejemplo 300 123 4567.")
    return digitos


def _clave(con) -> bytes:
    fila = con.execute("SELECT valor FROM secretos WHERE nombre = 'reportes'").fetchone()
    if fila:
        return fila["valor"]
    clave = secrets.token_bytes(32)
    con.execute("INSERT OR IGNORE INTO secretos (nombre, valor) VALUES ('reportes', ?)", (clave,))
    return con.execute("SELECT valor FROM secretos WHERE nombre = 'reportes'").fetchone()["valor"]


def _referencia(con, numero: str) -> str:
    return hmac.new(_clave(con), numero.encode(), hashlib.sha256).hexdigest()


def _personas_que_reportaron(con, ref: str) -> int:
    return con.execute(
        "SELECT COUNT(DISTINCT usuario_id) FROM reportes WHERE numero_ref = ? AND creado > ?",
        (ref, time.time() - VIGENCIA_REPORTE),
    ).fetchone()[0]


def reputacion(numero: str) -> int:
    """Número de personas distintas que reportaron este número en la ventana vigente."""
    with conexion() as con:
        return _personas_que_reportaron(con, _referencia(con, normalizar_numero(numero)))


def explicar(personas: int) -> dict:
    if personas == 0:
        return {
            "estado": "sin_reportes",
            "mensaje": "Nadie ha reportado este número en Centinela. Eso no garantiza que sea seguro.",
        }
    quien = "1 persona" if personas == 1 else f"{personas} personas"
    return {
        "estado": "reportado" if personas < UMBRAL_SENAL else "varios_reportes",
        "mensaje": (
            f"{quien} reportó este número como posible estafa. " if personas == 1 else
            f"{quien} reportaron este número como posible estafa. "
        ) + "Un reporte no confirma que lo sea: si te piden algo, cuelga y verifica por el canal oficial.",
    }


# ---- Rutas ----

router = APIRouter(tags=["reportes"])
limite_consultas = LimitePorCliente(maximo=30, ventana=60)


class Numero(BaseModel):
    numero: str = Field(min_length=1, max_length=25)


class NuevoReporte(Numero):
    categoria: Categoria


def _numero_o_422(numero: str) -> str:
    try:
        return normalizar_numero(numero)
    except NumeroInvalido as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/reportes/categorias")
def categorias():
    return [{"id": k, "descripcion": v} for k, v in CATEGORIAS.items()]


# POST y no GET para que el número no quede en los registros de acceso del servidor
@router.post("/numeros/consulta", dependencies=[Depends(limite_consultas)])
def consultar_numero(datos: Numero):
    numero = _numero_o_422(datos.numero)
    with conexion() as con:
        personas = _personas_que_reportaron(con, _referencia(con, numero))
    return {"reportes": personas, **explicar(personas)}


@router.post("/reportes", status_code=201, dependencies=[Depends(exigir_cabecera)])
def reportar(datos: NuevoReporte, sesion: Sesion = Depends(usuario_actual)):
    numero = _numero_o_422(datos.numero)
    ahora = time.time()
    with conexion() as con:
        hoy = con.execute(
            "SELECT COUNT(*) FROM reportes WHERE usuario_id = ? AND creado > ?", (sesion.usuario_id, ahora - 86400)
        ).fetchone()[0]
        if hoy >= MAX_REPORTES_POR_DIA:
            raise HTTPException(status_code=429, detail="Llegaste al máximo de 10 reportes por día.")
        ref = _referencia(con, numero)
        if con.execute(
            "SELECT 1 FROM reportes WHERE usuario_id = ? AND numero_ref = ?", (sesion.usuario_id, ref)
        ).fetchone():
            raise HTTPException(status_code=409, detail="Ya reportaste este número.")
        reporte_id = uuid.uuid4().hex
        con.execute(
            "INSERT INTO reportes (id, usuario_id, numero_ref, terminacion, categoria, creado) VALUES (?, ?, ?, ?, ?, ?)",
            (reporte_id, sesion.usuario_id, ref, numero[-4:], datos.categoria, ahora),
        )
        personas = _personas_que_reportaron(con, ref)
    log.info("cuenta=%s reporte=%s categoria=%s", sesion.usuario_id, reporte_id, datos.categoria)
    return {"id": reporte_id, "reportes": personas, **explicar(personas)}


def mis_reportes(con, usuario_id: str) -> list[dict]:
    filas = con.execute(
        "SELECT id, terminacion, categoria, creado FROM reportes WHERE usuario_id = ? ORDER BY creado DESC",
        (usuario_id,),
    ).fetchall()
    return [
        {"id": f["id"], "terminacion": f["terminacion"], "categoria": f["categoria"],
         "descripcion": CATEGORIAS.get(f["categoria"], f["categoria"]), "creado": f["creado"]}
        for f in filas
    ]


@router.get("/reportes/mios")
def ver_mis_reportes(sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        return mis_reportes(con, sesion.usuario_id)


@router.delete("/reportes/{reporte_id}", dependencies=[Depends(exigir_cabecera)])
def retirar_reporte(reporte_id: str, sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        n = con.execute("DELETE FROM reportes WHERE id = ? AND usuario_id = ?", (reporte_id, sesion.usuario_id)).rowcount
    if not n:
        raise HTTPException(status_code=404, detail="Reporte no encontrado")
    log.info("cuenta=%s reporte_retirado", sesion.usuario_id)
    return {"ok": True}
