"""Carga y valida los guiones anotados de datos/guiones/ (el formato está en esquema.json)."""
import json
from dataclasses import dataclass
from pathlib import Path

RUTA = Path(__file__).resolve().parents[2] / "datos" / "guiones" / "guiones.json"
# Guiones con modismos de varias regiones de Colombia; nunca se usan para entrenar
RUTA_REGIONALES = RUTA.with_name("guiones-regionales.json")
# Generados desde plantillas.json con evaluacion.generar_guiones
RUTA_SINTETICOS = RUTA.with_name("guiones-sinteticos.json")
ETIQUETAS = ("riesgo", "legitima")
PARTICIONES = ("desarrollo", "reservada", "regional", "sintetica_desarrollo", "sintetica_prueba")
# Particiones que el clasificador puede usar para entrenar
PARTICIONES_ENTRENAMIENTO = ("desarrollo", "sintetica_desarrollo")
# escrito: a mano por el equipo; plantilla: generado; piloto: transcrito de una llamada del piloto, con consentimiento
FUENTES = ("escrito", "plantilla", "piloto")
HABLANTES = ("llamante", "usuario")


@dataclass(frozen=True)
class Turno:
    hablante: str
    texto: str


@dataclass(frozen=True)
class Guion:
    id: str
    etiqueta: str
    categoria: str
    particion: str
    descripcion: str
    turno_riesgo: int | None
    turnos: tuple[Turno, ...]
    region: str | None = None
    fuente: str = "escrito"
    plantilla: str | None = None

    @property
    def es_riesgo(self) -> bool:
        return self.etiqueta == "riesgo"


class GuionInvalido(ValueError):
    pass


def _validar(d: dict) -> Guion:
    gid = d.get("id", "?")
    if d.get("etiqueta") not in ETIQUETAS:
        raise GuionInvalido(f"{gid}: etiqueta debe ser {ETIQUETAS}")
    if d.get("particion") not in PARTICIONES:
        raise GuionInvalido(f"{gid}: particion debe ser {PARTICIONES}")
    if d.get("fuente", "escrito") not in FUENTES:
        raise GuionInvalido(f"{gid}: fuente debe ser {FUENTES}")
    turnos = tuple(Turno(h, t) for h, t in d.get("turnos", []))
    if not turnos or any(t.hablante not in HABLANTES or not t.texto.strip() for t in turnos):
        raise GuionInvalido(f"{gid}: turnos vacíos o con hablante desconocido")
    riesgo = d.get("turno_riesgo")
    if d["etiqueta"] == "riesgo":
        if not isinstance(riesgo, int) or not 0 <= riesgo < len(turnos) or turnos[riesgo].hablante != "llamante":
            raise GuionInvalido(f"{gid}: turno_riesgo debe señalar un turno de quien llama")
    elif riesgo is not None:
        raise GuionInvalido(f"{gid}: una llamada legítima no tiene turno_riesgo")
    return Guion(gid, d["etiqueta"], d.get("categoria", ""), d["particion"], d.get("descripcion", ""), riesgo, turnos,
                 d.get("region"), d.get("fuente", "escrito"), d.get("plantilla"))


def cargar(ruta: Path | None = None, particion: str | None = None) -> list[Guion]:
    rutas = [Path(ruta)] if ruta else [RUTA, RUTA_REGIONALES, RUTA_SINTETICOS]
    datos = [d for r in rutas if r.exists() for d in json.loads(r.read_text(encoding="utf-8"))]
    guiones = [_validar(d) for d in datos]
    ids = [g.id for g in guiones]
    if len(ids) != len(set(ids)):
        raise GuionInvalido("Hay ids de guion repetidos")
    if particion and particion != "todas":
        guiones = [g for g in guiones if g.particion == particion]
    return guiones
