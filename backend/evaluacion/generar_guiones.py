"""Genera guiones sintéticos a partir de plantillas y variantes regionales.

    python -m evaluacion.generar_guiones            # escribe datos/guiones/guiones-sinteticos.json
    python -m evaluacion.generar_guiones --revisar  # falla si el archivo no coincide con las plantillas

Cada plantilla de datos/guiones/plantillas.json se llena una vez por región con
modismos de esa región (saludo, trato, forma de pedir, montos...). La elección es
fija para cada pareja plantilla-región, así que el resultado no cambia entre corridas.
Las plantillas de uso "entrenamiento" van a la partición sintetica_desarrollo y las
de uso "prueba" a sintetica_prueba, que nunca se usa para entrenar.
"""
import argparse
import json
import random
import re
import sys
import unicodedata
from pathlib import Path

from . import guiones

PLANTILLAS = guiones.RUTA.with_name("plantillas.json")
PARTICION_POR_USO = {"entrenamiento": "sintetica_desarrollo", "prueba": "sintetica_prueba"}
_HUECO = re.compile(r"\{(\w+)\}")


def _slug(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", sin_tildes.lower()).strip("-")


def _llenar(plantilla: dict, region: str, variantes: dict, comunes: dict) -> dict:
    azar = random.Random(f"{plantilla['id']}|{region}")
    elegidos = {}

    def valor(m):
        hueco = m.group(1)
        if hueco not in elegidos:
            opciones = variantes.get(hueco) or comunes.get(hueco)
            if not opciones:
                raise KeyError(f"{plantilla['id']}: no hay variantes para {{{hueco}}}")
            elegidos[hueco] = azar.choice(opciones)
        return elegidos[hueco]

    turnos = []
    for hablante, texto in plantilla["turnos"]:
        lleno = re.sub(r"\b(de|a) el\b", lambda m: m.group(1) + "l", _HUECO.sub(valor, texto))
        lleno = re.sub(r"([?!])[.,]", r"\1", lleno)  # "¿cómo va?." -> "¿cómo va?"
        turnos.append([hablante, lleno[:1].upper() + lleno[1:]])
    guion = {
        "id": f"s-{plantilla['id']}-{_slug(region)}",
        "etiqueta": plantilla["etiqueta"],
        "categoria": plantilla["categoria"],
        "particion": PARTICION_POR_USO[plantilla["uso"]],
        "region": region,
        "fuente": "plantilla",
        "plantilla": plantilla["id"],
        "descripcion": plantilla["descripcion"],
    }
    if plantilla["etiqueta"] == "riesgo":
        guion["turno_riesgo"] = plantilla["turno_riesgo"]
    guion["turnos"] = turnos
    return guion


def generar(ruta: Path = PLANTILLAS) -> list[dict]:
    datos = json.loads(Path(ruta).read_text(encoding="utf-8"))
    salida = [
        _llenar(p, region, variantes, datos["comunes"])
        for p in datos["plantillas"]
        for region, variantes in datos["regiones"].items()
    ]
    for g in salida:
        guiones._validar(g)
    return salida


def como_texto(lista: list[dict]) -> str:
    # Un guion por bloque y un turno por línea, para que los cambios se lean bien en git
    bloques = []
    for g in lista:
        cabecera = json.dumps({k: v for k, v in g.items() if k != "turnos"}, ensure_ascii=False)[:-1]
        turnos = ",\n".join("      " + json.dumps(t, ensure_ascii=False) for t in g["turnos"])
        bloques.append(f"  {cabecera},\n    \"turnos\": [\n{turnos}\n    ]\n  }}")
    return "[\n" + ",\n".join(bloques) + "\n]\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--revisar", action="store_true", help="No escribe; falla si el archivo está desactualizado")
    args = p.parse_args(argv)
    texto = como_texto(generar())
    if args.revisar:
        actual = guiones.RUTA_SINTETICOS.read_text(encoding="utf-8") if guiones.RUTA_SINTETICOS.exists() else ""
        if actual != texto:
            print("guiones-sinteticos.json no coincide con plantillas.json; corra python -m evaluacion.generar_guiones")
            sys.exit(1)
        print("guiones-sinteticos.json está al día")
        return
    guiones.RUTA_SINTETICOS.write_text(texto, encoding="utf-8")
    print(f"{texto.count('\"id\"')} guiones en {guiones.RUTA_SINTETICOS}")


if __name__ == "__main__":
    main()
