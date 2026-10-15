"""Reporte comunitario de números.

- Los reportes son seudónimos: nadie más que el autor ve quién reportó (A16).
- El número se guarda como HMAC con una clave local, no en claro; solo se guardan
  sus últimos 4 dígitos para que el autor reconozca sus propios reportes.
- Cada cuenta reporta un número una sola vez y como máximo 10 números por día (A15).
- La reputación es una señal de contexto más; nunca decide sola y "reportado" no
  significa "confirmado" (A15).
- Contra falsos positivos y reportes por odio masivo (A22), cada reporte tiene un peso:
  cuentas con menos de un día no cuentan todavía, por número solo cuentan los primeros
  3 reportes de cada día, los reportes viejos pesan menos, quien perdió algo pesa más
  que quien solo recibió el intento, y un reporte respaldado por una conversación que
  Centinela marcó alto o crítico pesa más. Las personas también pueden decir que la
  llamada fue legítima o que era publicidad: eso resta o separa, no suma como estafa.
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
# Puntaje de estafa necesario para que la reputación pese en el análisis
UMBRAL_SENAL = 2
# Para decir "estafa confirmada por la comunidad"
UMBRAL_CONFIRMADA = 3
MIN_PERDIDAS_CONFIRMADA = 2
# Una cuenta recién creada no cuenta hasta que tenga un día (frena cuentas de usar y tirar)
ANTIGUEDAD_MINIMA = 86400
# Por número, solo cuentan los primeros reportes de cada día (frena avalanchas)
MAX_QUE_CUENTAN_POR_DIA = 3
MEDIA_VIDA = 90 * 86400
PESOS = {"perdida": 1.5, "intento": 1.0, "publicidad": 1.0, "legitima": 1.0}
PESO_RESPALDO = 1.5

RESULTADOS = {
    "perdida": "Me estafaron: perdí dinero, datos o el control de una cuenta",
    "intento": "Intentaron estafarme, pero no caí",
    "publicidad": "Era publicidad, cobranza o un call center insistente, no una estafa",
    "legitima": "Era una llamada legítima",
}
Resultado = Literal["perdida", "intento", "publicidad", "legitima"]
ES_ESTAFA = ("perdida", "intento")

# Lo asigna main.py: dice si una conversación analizada respalda el reporte
respaldo_de_llamada = None
# La asigna main: deduce la categoría de un reporte a partir de la llamada analizada
categoria_de_llamada = None

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


def _pesar(con, ref: str, ahora: float | None = None) -> dict:
    """Suma los reportes vigentes de un número con sus pesos."""
    ahora = ahora or time.time()
    filas = con.execute(
        """SELECT r.usuario_id, r.resultado, r.respaldado, r.creado, u.creado AS cuenta_creada
           FROM reportes r JOIN usuarios u ON u.id = r.usuario_id
           WHERE r.numero_ref = ? AND r.creado > ? ORDER BY r.creado""",
        (ref, ahora - VIGENCIA_REPORTE),
    ).fetchall()
    total = {"estafa": 0.0, "publicidad": 0.0, "legitima": 0.0}
    personas, perdidas, en_espera = set(), set(), 0
    por_dia: dict[int, int] = {}
    for f in filas:
        dia = int(f["creado"] // 86400)
        por_dia[dia] = por_dia.get(dia, 0) + 1
        if f["creado"] - f["cuenta_creada"] < ANTIGUEDAD_MINIMA and ahora - f["cuenta_creada"] < ANTIGUEDAD_MINIMA:
            en_espera += 1
            continue
        if por_dia[dia] > MAX_QUE_CUENTAN_POR_DIA:
            en_espera += 1
            continue
        peso = PESOS[f["resultado"]] * 0.5 ** ((ahora - f["creado"]) / MEDIA_VIDA)
        if f["respaldado"]:
            peso *= PESO_RESPALDO
        if f["resultado"] in ES_ESTAFA:
            total["estafa"] += peso
            personas.add(f["usuario_id"])
            if f["resultado"] == "perdida":
                perdidas.add(f["usuario_id"])
        else:
            total[f["resultado"]] += peso
    return {
        "puntaje": round(total["estafa"], 2),
        "publicidad": round(total["publicidad"], 2),
        "legitima": round(total["legitima"], 2),
        "personas": len(personas),
        "perdidas": len(perdidas),
        "en_espera": en_espera,
    }


def _estado(p: dict) -> str:
    if not p["personas"] and not p["publicidad"] and not p["legitima"]:
        return "en_revision" if p["en_espera"] else "sin_reportes"
    if p["legitima"] and p["legitima"] >= p["puntaje"] / 2:
        return "en_disputa"
    if p["publicidad"] > p["puntaje"]:
        return "publicidad"
    if p["puntaje"] >= UMBRAL_CONFIRMADA and p["perdidas"] >= MIN_PERDIDAS_CONFIRMADA:
        return "estafa_confirmada"
    if p["puntaje"] >= UMBRAL_SENAL:
        return "varios_reportes"
    return "reportado"


# Estados en los que el número cuenta como señal de contexto en el análisis
ESTADOS_CON_SENAL = ("varios_reportes", "estafa_confirmada")


def explicar(p: dict) -> dict:
    estado = _estado(p)
    n = p["personas"]
    quien = "1 persona" if n == 1 else f"{n} personas"
    mensajes = {
        "sin_reportes": "Nadie ha reportado este número en Centinela. Eso no garantiza que sea seguro.",
        "en_revision": "Hay reportes recientes de cuentas nuevas que todavía no cuentan. Si te piden algo, cuelga y verifica por el canal oficial.",
        "en_disputa": "Hay reportes que se contradicen: unas personas dicen que fue estafa y otras que fue una llamada legítima. Si te piden algo, verifica por el canal oficial.",
        "publicidad": "Las personas que lo reportaron dicen que es publicidad, cobranza o un call center, no una estafa.",
        "reportado": f"{quien} {'reportó' if n == 1 else 'reportaron'} este número como posible estafa. Un reporte no confirma que lo sea: si te piden algo, cuelga y verifica por el canal oficial.",
        "varios_reportes": f"{quien} reportaron este número como posible estafa. No está confirmado: si te piden algo, cuelga y verifica por el canal oficial.",
        "estafa_confirmada": f"Probable estafa: {p['perdidas']} personas dicen que perdieron dinero o datos con este número. No entregues nada; cuelga y verifica por el canal oficial.",
    }
    return {"estado": estado, "mensaje": mensajes[estado], "senal": estado in ESTADOS_CON_SENAL}


def referencia(numero: str) -> str:
    with conexion() as con:
        return _referencia(con, normalizar_numero(numero))


def reputacion(numero: str) -> dict:
    """Reputación ponderada del número: cuántas personas cuentan, puntaje y estado."""
    with conexion() as con:
        ref = _referencia(con, normalizar_numero(numero))
        p = _pesar(con, ref)
    return {"ref": ref, "reportes": p["personas"], **explicar(p)}


# ---- Rutas ----

router = APIRouter(tags=["reportes"])
limite_consultas = LimitePorCliente(maximo=30, ventana=60)


class Numero(BaseModel):
    numero: str = Field(min_length=1, max_length=25)


class NuevoReporte(Numero):
    resultado: Resultado = "intento"
    # Qué hizo; no aplica si fue legítima o publicidad
    categoria: Categoria | None = None
    # Conversación analizada en Centinela durante esa llamada, si la hubo
    llamada_id: str | None = Field(default=None, max_length=64)


def _numero_o_422(numero: str) -> str:
    try:
        return normalizar_numero(numero)
    except NumeroInvalido as e:
        raise HTTPException(status_code=422, detail=str(e))


@router.get("/reportes/categorias")
def categorias():
    return [{"id": k, "descripcion": v} for k, v in CATEGORIAS.items()]


@router.get("/reportes/resultados")
def resultados():
    return [{"id": k, "descripcion": v} for k, v in RESULTADOS.items()]


# POST y no GET para que el número no quede en los registros de acceso del servidor
@router.post("/numeros/consulta", dependencies=[Depends(limite_consultas)])
def consultar_numero(datos: Numero):
    numero = _numero_o_422(datos.numero)
    with conexion() as con:
        p = _pesar(con, _referencia(con, numero))
    return {"reportes": p["personas"], **explicar(p)}


@router.post("/reportes", status_code=201, dependencies=[Depends(exigir_cabecera)])
def reportar(datos: NuevoReporte, sesion: Sesion = Depends(usuario_actual)):
    numero = _numero_o_422(datos.numero)
    categoria = datos.categoria
    if datos.resultado in ES_ESTAFA and not categoria and datos.llamada_id and categoria_de_llamada:
        # Reporte de un toque al colgar: la categoría sale de lo que Centinela detectó
        categoria = categoria_de_llamada(datos.llamada_id, sesion.usuario_id)
    if datos.resultado in ES_ESTAFA and not categoria:
        raise HTTPException(status_code=422, detail="Cuéntanos qué hizo quien llamó.")
    categoria = categoria if datos.resultado in ES_ESTAFA else "ninguna"
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
        respaldado = bool(
            datos.llamada_id and datos.resultado in ES_ESTAFA and respaldo_de_llamada
            and respaldo_de_llamada(datos.llamada_id, sesion.usuario_id, ref)
        )
        reporte_id = uuid.uuid4().hex
        con.execute(
            """INSERT INTO reportes (id, usuario_id, numero_ref, terminacion, categoria, creado, resultado, respaldado)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (reporte_id, sesion.usuario_id, ref, numero[-4:], categoria, ahora, datos.resultado, int(respaldado)),
        )
        p = _pesar(con, ref)
        cuenta_nueva = ahora - con.execute(
            "SELECT creado FROM usuarios WHERE id = ?", (sesion.usuario_id,)
        ).fetchone()[0] < ANTIGUEDAD_MINIMA
    log.info("cuenta=%s reporte=%s resultado=%s respaldado=%s", sesion.usuario_id, reporte_id, datos.resultado, respaldado)
    return {"id": reporte_id, "reportes": p["personas"], "respaldado": respaldado,
            "cuenta_nueva": cuenta_nueva, **explicar(p)}


def mis_reportes(con, usuario_id: str) -> list[dict]:
    filas = con.execute(
        "SELECT id, terminacion, categoria, resultado, respaldado, creado FROM reportes WHERE usuario_id = ? ORDER BY creado DESC",
        (usuario_id,),
    ).fetchall()
    return [
        {"id": f["id"], "terminacion": f["terminacion"], "categoria": f["categoria"],
         "resultado": f["resultado"], "respaldado": bool(f["respaldado"]),
         "descripcion": CATEGORIAS.get(f["categoria"]) or RESULTADOS[f["resultado"]], "creado": f["creado"]}
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
