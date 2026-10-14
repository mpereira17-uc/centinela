from fastapi import FastAPI, HTTPException

from .config import ajustes
from .estrategias import Acumulacion, PorFragmento
from .modelos import Fragmento, FragmentoEntrada, Llamada

app = FastAPI(
    title="Centinela",
    description="Prototipo de alertas de posible fraude conversacional en llamadas simuladas.",
    version="0.1.0",
)

estrategias = [
    PorFragmento(ajustes.umbral),
    Acumulacion(ajustes.umbral, ajustes.limite_contexto),
]

# Registro en memoria; pasará a SQLite cuando se defina el modelo de datos (Fase 2)
llamadas: dict[str, Llamada] = {}


@app.get("/salud")
def salud():
    return {"estado": "ok", "estrategia_visible": ajustes.estrategia_visible}


@app.post("/llamadas", response_model=Llamada, status_code=201)
def crear_llamada():
    llamada = Llamada()
    llamadas[llamada.id] = llamada
    return llamada


@app.get("/llamadas/{llamada_id}", response_model=Llamada)
def ver_llamada(llamada_id: str):
    return _buscar(llamada_id)


@app.post("/llamadas/{llamada_id}/fragmentos")
def agregar_fragmento(llamada_id: str, entrada: FragmentoEntrada):
    llamada = _buscar(llamada_id)
    historial = [f.texto for f in llamada.fragmentos]
    fragmento = Fragmento(**entrada.model_dump())
    # Ambas estrategias deciden sobre el mismo diálogo; el registro guarda las dos
    fragmento.decisiones = [e.decidir(historial, entrada.texto) for e in estrategias]
    llamada.fragmentos.append(fragmento)

    visible = next(d for d in fragmento.decisiones if d.estrategia == ajustes.estrategia_visible)
    mostrar_aviso = visible.alerta and not llamada.aviso_visible
    if mostrar_aviso:
        llamada.aviso_visible = True
    return {"fragmento": fragmento, "mostrar_aviso": mostrar_aviso}


def _buscar(llamada_id: str) -> Llamada:
    if llamada_id not in llamadas:
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return llamadas[llamada_id]
