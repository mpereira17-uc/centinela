import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles

from .config import ajustes
from .estrategias import Acumulacion, PorFragmento
from .modelos import MAX_FRAGMENTOS_POR_LLAMADA, Fragmento, FragmentoEntrada, Llamada
from .senales import CATALOGO, Nivel

# Nunca se registra el texto de la conversación (modelo de amenazas, A8)
log = logging.getLogger("centinela")

app = FastAPI(
    title="Centinela",
    description="Prototipo de alertas de posible fraude conversacional en llamadas simuladas.",
    version="0.2.0",
)

_nivel_alerta = Nivel[ajustes.nivel_alerta.upper()]
estrategias = [
    PorFragmento(_nivel_alerta),
    Acumulacion(_nivel_alerta, ajustes.limite_contexto),
]

FRONTEND = Path(__file__).resolve().parents[2] / "frontend"

# Cabeceras de seguridad para la interfaz (modelo de amenazas, A5)
CABECERAS_SEGURIDAD = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; "
        "connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "Permissions-Policy": "camera=(), geolocation=(), microphone=()",
}


@app.middleware("http")
async def cabeceras_de_seguridad(request: Request, call_next):
    respuesta = await call_next(request)
    respuesta.headers.update(CABECERAS_SEGURIDAD)
    return respuesta


# Registro en memoria; pasará a SQLite en el paso 7 de la hoja de ruta
MAX_LLAMADAS = 1000
llamadas: dict[str, Llamada] = {}


@app.get("/salud")
def salud():
    return {"estado": "ok", "estrategia_visible": ajustes.estrategia_visible}


@app.get("/senales")
def catalogo_de_senales():
    """Lista pública de las señales que el motor revisa, para explicar las alertas."""
    return [{"id": s.id, "tipo": s.tipo, "descripcion": s.descripcion} for s in CATALOGO]


@app.post("/llamadas", response_model=Llamada, status_code=201)
def crear_llamada():
    if len(llamadas) >= MAX_LLAMADAS:
        raise HTTPException(status_code=429, detail="Se alcanzó el máximo de llamadas en memoria")
    llamada = Llamada()
    llamadas[llamada.id] = llamada
    return llamada


@app.get("/llamadas/{llamada_id}", response_model=Llamada)
def ver_llamada(llamada_id: str):
    return _buscar(llamada_id)


@app.post("/llamadas/{llamada_id}/fragmentos")
def agregar_fragmento(llamada_id: str, entrada: FragmentoEntrada):
    llamada = _buscar(llamada_id)
    if len(llamada.fragmentos) >= MAX_FRAGMENTOS_POR_LLAMADA:
        raise HTTPException(status_code=413, detail="La llamada superó el máximo de fragmentos")

    historial = [f.texto for f in llamada.fragmentos]
    fragmento = Fragmento(**entrada.model_dump())
    # Ambas estrategias deciden sobre el mismo diálogo; el registro guarda las dos
    fragmento.decisiones = [e.decidir(historial, entrada.texto) for e in estrategias]
    llamada.fragmentos.append(fragmento)

    visible = next(d for d in fragmento.decisiones if d.estrategia == ajustes.estrategia_visible)
    mostrar_aviso = visible.alerta and not llamada.aviso_visible
    if mostrar_aviso:
        llamada.aviso_visible = True

    log.info(
        "llamada=%s fragmento=%s niveles=%s aviso=%s",
        llamada.id,
        fragmento.id,
        ",".join(f"{d.estrategia}:{d.nivel}" for d in fragmento.decisiones),
        mostrar_aviso,
    )
    return {"fragmento": fragmento, "mostrar_aviso": mostrar_aviso, "decision_visible": visible}


def _buscar(llamada_id: str) -> Llamada:
    if llamada_id not in llamadas:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return llamadas[llamada_id]


# La interfaz se sirve al final para que las rutas de la API tengan prioridad
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="interfaz")
