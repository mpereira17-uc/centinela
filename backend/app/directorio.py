"""Directorio de canales oficiales para verificar una llamada o un mensaje.

La regla de oro: cuelga y contacta tú a la entidad por un canal que no te dio quien llamó.
Solo hay teléfonos confirmados en fuentes oficiales; para los bancos, el número correcto
es el del respaldo de la tarjeta o el de la aplicación oficial (docs/directorio.md).
"""
import json
from functools import lru_cache
from pathlib import Path

from fastapi import APIRouter

RUTA = Path(__file__).resolve().parents[2] / "datos" / "directorio" / "directorio.json"
TIPOS = {
    "emergencia": "Emergencias y denuncias",
    "banco": "Bancos",
    "billetera": "Billeteras digitales",
    "gobierno": "Entidades del Estado",
    "mensajeria": "Mensajería",
    "operador": "Operadores de celular",
}
CONSEJO_BANCOS = "Llama al número que está al respaldo de tu tarjeta o en la aplicación oficial del banco, nunca al que te dieron en la llamada o en el mensaje."

router = APIRouter(tags=["directorio"])


@lru_cache(maxsize=1)
def cargar() -> dict:
    return json.loads(RUTA.read_text(encoding="utf-8"))


@router.get("/directorio")
def directorio():
    datos = cargar()
    grupos = []
    for tipo, titulo in TIPOS.items():
        entradas = [e for e in datos["entradas"] if e["tipo"] == tipo]
        if entradas:
            grupo = {"tipo": tipo, "titulo": titulo, "entradas": entradas}
            if tipo in ("banco", "billetera"):
                grupo["consejo"] = CONSEJO_BANCOS
            grupos.append(grupo)
    return {"actualizado": datos["actualizado"], "grupos": grupos}
