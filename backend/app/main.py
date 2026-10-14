import logging
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles

from .config import ajustes
from .estrategias import Acumulacion, PorFragmento
from .modelos import MAX_FRAGMENTOS_POR_LLAMADA, Fragmento, FragmentoEntrada, Llamada
from .senales import CATALOGO, Nivel
from .transcripcion import whisper

# Nunca se registra el texto de la conversación (modelo de amenazas, A8)
log = logging.getLogger("centinela")

app = FastAPI(
    title="Centinela",
    description="Prototipo de alertas de posible fraude conversacional en llamadas simuladas.",
    version="0.4.0",
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
    "Permissions-Policy": "camera=(), geolocation=(), microphone=(self)",
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
    return _procesar(_buscar(llamada_id), entrada)


# Límites del audio (modelo de amenazas, A6)
MAX_AUDIO_BYTES = 10 * 1024 * 1024
TIPOS_AUDIO = ("audio/", "video/webm", "video/mp4", "application/octet-stream")


@app.post("/llamadas/{llamada_id}/audio")
async def agregar_audio(
    llamada_id: str,
    audio: UploadFile = File(...),
    consentimiento: bool = Form(...),
    hablante: str | None = Form(default=None, max_length=50),
):
    """Transcribe un audio en este equipo y analiza cada segmento como un fragmento.

    El audio se lee en memoria y se descarta al terminar; no se guarda.
    """
    llamada = _buscar(llamada_id)
    if not consentimiento:
        raise HTTPException(status_code=400, detail="Se necesita el consentimiento de las personas grabadas")
    if not (audio.content_type or "").startswith(TIPOS_AUDIO):
        raise HTTPException(status_code=415, detail="El archivo no es de audio")

    datos = await audio.read(MAX_AUDIO_BYTES + 1)
    await audio.close()
    if len(datos) > MAX_AUDIO_BYTES:
        raise HTTPException(status_code=413, detail="El audio supera los 10 MB")
    if not datos:
        raise HTTPException(status_code=400, detail="El audio está vacío")

    try:
        # La transcripción es lenta y bloqueante: se ejecuta fuera del bucle de eventos
        segmentos = await run_in_threadpool(whisper.transcribir, datos)
    except whisper.TranscripcionNoDisponible as e:
        raise HTTPException(status_code=503, detail=str(e))
    except whisper.AudioInvalido as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        del datos

    # Los tiempos del audio se desplazan para continuar después de lo ya analizado
    desfase = llamada.fragmentos[-1].fin if llamada.fragmentos else 0.0
    resultados = []
    for seg in segmentos:
        entrada = FragmentoEntrada(
            texto=seg.texto[:2000], inicio=desfase + seg.inicio, fin=desfase + max(seg.fin, seg.inicio), hablante=hablante
        )
        resultados.append(_procesar(llamada, entrada))
    log.info("llamada=%s audio_segmentos=%d", llamada.id, len(resultados))
    return {"resultados": resultados, "mostrar_aviso": any(r["mostrar_aviso"] for r in resultados)}


def _procesar(llamada: Llamada, entrada: FragmentoEntrada) -> dict:
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
