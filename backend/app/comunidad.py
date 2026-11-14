"""Tablero de la comunidad: lo que reportaron las personas en la última semana, solo con totales.

- No muestra quién reportó, ni números, ni terminaciones: solo conteos por resultado y por
  modalidad (Ley 1581). Ningún total permite llegar a una persona.
- Cuenta todos los reportes que llegaron, también los de cuentas nuevas que todavía no pesan en la
  reputación de un número: el tablero dice cuántos llegaron, no que estén confirmados.
- Si hay datos de ejemplo de la demostración (app/demo.py), dice cuántos son, para no hacerlos
  pasar por reportes reales.
"""
import time

from fastapi import APIRouter, Depends, Response

from .cuentas import LimitePorCliente
from .db import conexion
from .demo import PREFIJO
from .reportes import ES_ESTAFA

DIAS = 7
# Nombres cortos para el tablero; la descripción larga está en reportes.CATEGORIAS
MODALIDADES = {
    "suplanta_entidad": "Falso banco o entidad",
    "premio_falso": "Premio, subsidio o inversión falsa",
    "familiar_falso": "Falso familiar o conocido",
    "extorsion": "Amenaza o extorsión",
    "soporte_falso": "Falso soporte técnico",
    "otro": "Otra modalidad",
}

router = APIRouter(tags=["comunidad"])
# La página se actualiza cada 10 segundos (6 por minuto); esto deja de sobra para varias pestañas
limite_tablero = LimitePorCliente(maximo=60, ventana=60)


def resumen(ahora: float | None = None) -> dict:
    desde = (ahora or time.time()) - DIAS * 86400
    with conexion() as con:
        filas = con.execute(
            """SELECT r.resultado, r.categoria, COUNT(*) AS n, SUM(u.alias LIKE ?) AS ejemplo
               FROM reportes r JOIN usuarios u ON u.id = r.usuario_id
               WHERE r.creado > ? GROUP BY r.resultado, r.categoria""",
            (PREFIJO + "%", desde),
        ).fetchall()
        numeros = con.execute(
            "SELECT COUNT(DISTINCT numero_ref) FROM reportes WHERE creado > ? AND resultado IN (?, ?)",
            (desde, *ES_ESTAFA),
        ).fetchone()[0]
        avisos = dict(con.execute(
            "SELECT resultado, COUNT(*) FROM desenlaces WHERE creado > ? AND aviso = 1 GROUP BY resultado", (desde,)
        ).fetchall())
    resultados = {"perdida": 0, "intento": 0, "publicidad": 0, "legitima": 0}
    modalidades = dict.fromkeys(MODALIDADES, 0)
    ejemplo = 0
    for f in filas:
        resultados[f["resultado"]] += f["n"]
        ejemplo += f["ejemplo"] or 0
        if f["resultado"] in ES_ESTAFA:
            clave = f["categoria"] if f["categoria"] in modalidades else "otro"
            modalidades[clave] += f["n"]
    return {
        "dias": DIAS,
        "estafa": resultados["perdida"] + resultados["intento"],
        "numeros": numeros,
        **resultados,
        # Ordenadas de la más a la menos reportada; las que no tienen reportes no se muestran
        "modalidades": [
            {"id": k, "nombre": MODALIDADES[k], "reportes": n}
            for k, n in sorted(modalidades.items(), key=lambda kv: -kv[1]) if n
        ],
        # De lo que contaron las personas al colgar una llamada en la que Centinela avisó
        "avisos": {"no_cayeron": avisos.get("intento", 0), "perdieron": avisos.get("perdida", 0)},
        "ejemplo": ejemplo,
    }


@router.get("/comunidad/tablero", dependencies=[Depends(limite_tablero)])
def tablero(respuesta: Response):
    respuesta.headers["Cache-Control"] = "no-store"
    return resumen()
