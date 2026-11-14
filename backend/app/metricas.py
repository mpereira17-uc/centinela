"""Cifras automáticas para el documento: cuándo avisó cada estrategia en cada llamada.

Por cada llamada analizada se guarda una fila sin texto, sin número y sin cuenta: cuántas
frases tuvo, en qué frase y en qué segundo avisó por primera vez cada estrategia, el nivel
máximo de cada una, cuánto tardó el servidor en responder y, si la persona lo contó al
colgar, cómo terminó. El identificador de la fila es aleatorio y no es el de la llamada,
así que no se puede unir con el historial de nadie.

    GET /metricas/resumen    los totales por estrategia (público, solo conteos)
    GET /metricas.csv        una fila por llamada, para el documento (pide la llave del presentador)
    python -m app.metricas   el mismo CSV, en la terminal del portátil
"""
import csv
import io
import json
import time

from fastapi import APIRouter, Header, Response

from .db import conexion
from .desenlaces import ES_ESTAFA, ORDEN

router = APIRouter(tags=["cifras"])


def _primeras_alertas(llamada) -> dict:
    primeras: dict = {}
    for i, f in enumerate(llamada.fragmentos, start=1):
        for d in f.decisiones:
            primeras.setdefault(d.estrategia, None)
            if d.alerta and primeras[d.estrategia] is None:
                primeras[d.estrategia] = {"frase": i, "segundo": round(f.fin, 1)}
    return primeras


def _niveles(llamada) -> dict:
    niveles: dict = {}
    for f in llamada.fragmentos:
        for d in f.decisiones:
            actual = niveles.get(d.estrategia, "bajo")
            niveles[d.estrategia] = max(actual, d.nivel, key=ORDEN.index)
    return niveles


def registrar(llamada, origen: str):
    """Guarda o actualiza la fila de la llamada después de cada frase."""
    tiempos = llamada.tiempos_respuesta
    with conexion() as con:
        con.execute(
            """INSERT INTO metricas_llamadas (id, creada, origen, proyectada, fragmentos, alertas, niveles, respuesta_media)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(id) DO UPDATE SET origen = excluded.origen, fragmentos = excluded.fragmentos,
                 alertas = excluded.alertas, niveles = excluded.niveles, respuesta_media = excluded.respuesta_media""",
            (
                llamada.metrica_id, llamada.creada.timestamp(), origen, int(llamada.proyectar), len(llamada.fragmentos),
                json.dumps(_primeras_alertas(llamada)), json.dumps(_niveles(llamada)),
                round(sum(tiempos) / len(tiempos), 3) if tiempos else None,
            ),
        )


def contar_desenlace(llamada, resultado: str):
    with conexion() as con:
        con.execute("UPDATE metricas_llamadas SET desenlace = ? WHERE id = ?", (resultado, llamada.metrica_id))


def _filas() -> list[dict]:
    with conexion() as con:
        filas = con.execute("SELECT * FROM metricas_llamadas ORDER BY creada").fetchall()
    return [{**dict(f), "alertas": json.loads(f["alertas"]), "niveles": json.loads(f["niveles"])} for f in filas]


def _media(valores: list[float]) -> float | None:
    return round(sum(valores) / len(valores), 2) if valores else None


@router.get("/metricas/resumen")
def resumen():
    """Por estrategia: cuántas llamadas avisó, en qué frase y segundo, y cómo cuadra con lo que contaron las personas."""
    filas = _filas()
    estrategias = sorted({e for f in filas for e in f["alertas"]})
    por_estrategia = {}
    for e in estrategias:
        avisos = [f["alertas"][e] for f in filas if f["alertas"].get(e)]
        con_desenlace = [f for f in filas if f["desenlace"]]
        avisada = lambda f: bool(f["alertas"].get(e))
        estafa = lambda f: f["desenlace"] in ES_ESTAFA
        por_estrategia[e] = {
            "llamadas_con_aviso": len(avisos),
            "frase_media_del_aviso": _media([a["frase"] for a in avisos]),
            "segundo_medio_del_aviso": _media([a["segundo"] for a in avisos]),
            "estafas_avisadas": sum(1 for f in con_desenlace if avisada(f) and estafa(f)),
            "estafas_sin_aviso": sum(1 for f in con_desenlace if not avisada(f) and estafa(f)),
            "falsas_alarmas": sum(1 for f in con_desenlace if avisada(f) and not estafa(f)),
            "normales_sin_aviso": sum(1 for f in con_desenlace if not avisada(f) and not estafa(f)),
        }
    return {
        "llamadas": len(filas),
        "con_desenlace": sum(1 for f in filas if f["desenlace"]),
        "respuesta_media_segundos": _media([f["respuesta_media"] for f in filas if f["respuesta_media"] is not None]),
        "por_estrategia": por_estrategia,
        "nota": "Cómo terminó lo cuentan las personas al colgar; no está verificado. Las llamadas de la demostración se marcan como proyectadas.",
    }


def csv_de_llamadas() -> str:
    filas = _filas()
    estrategias = sorted({e for f in filas for e in f["alertas"]})
    salida = io.StringIO()
    escritor = csv.writer(salida)
    escritor.writerow(
        ["fecha", "origen", "proyectada", "frases", "desenlace", "respuesta_media_s"]
        + [c for e in estrategias for c in (f"{e}_frase_aviso", f"{e}_segundo_aviso", f"{e}_nivel_max")]
    )
    for f in filas:
        fila = [time.strftime("%Y-%m-%d %H:%M", time.localtime(f["creada"])), f["origen"], f["proyectada"], f["fragmentos"],
                f["desenlace"] or "", f["respuesta_media"] if f["respuesta_media"] is not None else ""]
        for e in estrategias:
            a = f["alertas"].get(e)
            fila += [a["frase"] if a else "", a["segundo"] if a else "", f["niveles"].get(e, "")]
        escritor.writerow(fila)
    return salida.getvalue()


@router.get("/metricas.csv")
def descargar(x_presentador: str | None = Header(default=None)):
    from .presentador import _autorizar

    _autorizar(x_presentador)
    return Response(csv_de_llamadas(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="centinela-cifras.csv"', "Cache-Control": "no-store"})


if __name__ == "__main__":
    print(csv_de_llamadas(), end="")
