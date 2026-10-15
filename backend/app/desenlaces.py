"""Cómo terminó una llamada: el feedback de quien la recibió, con un toque al colgar.

Se guarda solo el nivel máximo que vio, si hubo aviso y lo que contó. No se guarda la
cuenta, el número ni el texto. Con eso se mide, con llamadas reales del piloto, cuántas
estafas avisó Centinela y cuántas llamadas normales alarmó por error.
"""
import time
import uuid
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from .db import conexion

ORDEN = ["bajo", "moderado", "alto", "critico"]
Desenlace = Literal["perdida", "intento", "publicidad", "legitima"]
ES_ESTAFA = ("perdida", "intento")
# Qué categoría de reporte corresponde a cada señal, de la más a la menos específica.
# La amenaza va al final: un falso banco también amenaza con "bloquear la cuenta".
CATEGORIA_POR_SENAL = [
    ("acceso_remoto", "soporte_falso"),
    ("finge_conocido", "familiar_falso"),
    ("premio_inversion", "premio_falso"),
    ("suplanta_entidad", "suplanta_entidad"),
    ("amenaza", "extorsion"),
]

router = APIRouter(tags=["desenlaces"])


class NuevoDesenlace(BaseModel):
    resultado: Desenlace


def nivel_maximo(niveles: list[str]) -> str:
    return max(niveles, key=ORDEN.index, default="bajo")


def categoria_por_senales(ids: set[str]) -> str:
    return next((c for s, c in CATEGORIA_POR_SENAL if s in ids), "otro")


def guardar(nivel_max: str, aviso: bool, resultado: str) -> None:
    with conexion() as con:
        con.execute(
            "INSERT INTO desenlaces (id, creado, nivel_max, aviso, resultado) VALUES (?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, time.time(), nivel_max, int(aviso), resultado),
        )


@router.get("/desenlaces/resumen")
def resumen():
    """Tabla de aciertos con lo que contaron las personas. Solo conteos."""
    with conexion() as con:
        filas = con.execute("SELECT aviso, resultado, COUNT(*) AS n FROM desenlaces GROUP BY aviso, resultado").fetchall()
    tabla = {"con_aviso": {"estafa": 0, "no_estafa": 0}, "sin_aviso": {"estafa": 0, "no_estafa": 0}}
    for f in filas:
        tabla["con_aviso" if f["aviso"] else "sin_aviso"]["estafa" if f["resultado"] in ES_ESTAFA else "no_estafa"] += f["n"]
    estafas = tabla["con_aviso"]["estafa"] + tabla["sin_aviso"]["estafa"]
    normales = tabla["con_aviso"]["no_estafa"] + tabla["sin_aviso"]["no_estafa"]
    return {
        "total": estafas + normales,
        "tabla": tabla,
        "estafas_avisadas": tabla["con_aviso"]["estafa"] / estafas if estafas else None,
        "falsas_alarmas": tabla["con_aviso"]["no_estafa"] / normales if normales else None,
        "nota": "Lo cuentan las personas al colgar; no está verificado.",
    }
