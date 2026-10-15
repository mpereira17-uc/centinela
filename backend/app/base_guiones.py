"""Base de guiones anotados, servida por una API de solo lectura.

    GET /guiones?etiqueta=riesgo&region=bogota&categoria=extorsion&desde=0&limite=50
    GET /guiones/resumen     cuántos hay por partición, etiqueta, categoría, región y fuente
    GET /guiones/esquema     el formato de cada guion (JSON Schema)

Lee los mismos archivos de datos/guiones/ que usan la evaluación y el entrenamiento,
así que la API y el modelo siempre ven la misma base. No guarda datos de usuarios.
"""
import json
from collections import Counter
from dataclasses import asdict
from functools import lru_cache
from typing import Literal

from fastapi import APIRouter, Depends, Query

from evaluacion import guiones

from .cuentas import LimitePorCliente

router = APIRouter(prefix="/guiones", tags=["guiones"])
limite_guiones = LimitePorCliente(maximo=60, ventana=60)
ESQUEMA = guiones.RUTA.with_name("esquema.json")


@lru_cache(maxsize=1)
def _base() -> tuple[dict, ...]:
    filas = []
    for g in guiones.cargar():
        fila = asdict(g)
        fila["turnos"] = [{"hablante": t.hablante, "texto": t.texto} for t in g.turnos]
        filas.append(fila)
    return tuple(filas)


@router.get("", dependencies=[Depends(limite_guiones)])
def listar(
    etiqueta: Literal["riesgo", "legitima"] | None = None,
    categoria: str | None = Query(None, max_length=40),
    region: str | None = Query(None, max_length=40),
    particion: Literal[guiones.PARTICIONES] | None = None,
    fuente: Literal[guiones.FUENTES] | None = None,
    desde: int = Query(0, ge=0),
    limite: int = Query(50, ge=1, le=200),
):
    filtros = {"etiqueta": etiqueta, "categoria": categoria, "region": region, "particion": particion, "fuente": fuente}
    elegidos = [g for g in _base() if all(v is None or g[k] == v for k, v in filtros.items())]
    return {"total": len(elegidos), "desde": desde, "limite": limite, "guiones": elegidos[desde:desde + limite]}


@router.get("/resumen", dependencies=[Depends(limite_guiones)])
def resumen():
    base = _base()
    contar = lambda campo: dict(Counter(g[campo] or "sin dato" for g in base).most_common())
    return {
        "total": len(base),
        **{f"por_{c}": contar(c) for c in ("particion", "etiqueta", "categoria", "region", "fuente")},
        "para_entrenar": list(guiones.PARTICIONES_ENTRENAMIENTO),
    }


@router.get("/esquema")
def esquema():
    return json.loads(ESQUEMA.read_text(encoding="utf-8"))
