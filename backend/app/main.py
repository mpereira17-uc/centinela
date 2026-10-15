import logging
from pathlib import Path

from fastapi import Depends, FastAPI, File, Form, HTTPException, Request, Response, UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.staticfiles import StaticFiles

from . import asistente, base_guiones, cuentas, historial, mensajes, reportes, senalizacion, voz
from .cuentas import Sesion, sesion_opcional
from .config import ajustes
from .modelos import (
    MAX_FRAGMENTOS_POR_LLAMADA,
    ConsultaAsistente,
    Fragmento,
    FragmentoEntrada,
    Llamada,
    NuevaLlamada,
    TextoParaVoz,
)
from .analisis import ESTRATEGIA_VISIBLE, estrategias
from .clasificador import PATRON_APRENDIDO
from .senales import CATALOGO, NUMERO_REPORTADO
from .transcripcion import whisper

# Nunca se registra el texto de la conversación (modelo de amenazas, A8)
log = logging.getLogger("centinela")

app = FastAPI(
    title="Centinela",
    description="Prototipo de alertas de posible fraude conversacional en llamadas simuladas.",
    version="1.0.0",
)


FRONTEND = Path(__file__).resolve().parents[2] / "frontend"

# Cabeceras de seguridad para la interfaz (modelo de amenazas, A5)
CABECERAS_SEGURIDAD = {
    "Content-Security-Policy": (
        "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; media-src 'self' blob:; "
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


# Llamadas activas en memoria; las de personas que lo permiten se copian al historial en SQLite
MAX_LLAMADAS = 1000
llamadas: dict[str, Llamada] = {}


def _respalda_reporte(llamada_id: str, usuario_id: str, ref: str) -> bool:
    """Un reporte queda respaldado si viene de una conversación sobre ese mismo número
    que Centinela marcó alto o crítico, y que no es de otra cuenta."""
    llamada = llamadas.get(llamada_id)
    if not llamada or llamada.numero_ref != ref or llamada.dueno not in (None, usuario_id):
        return False
    niveles = {d.nivel for f in llamada.fragmentos for d in f.decisiones if d.estrategia == ESTRATEGIA_VISIBLE}
    return bool(niveles & {"alto", "critico"})


reportes.respaldo_de_llamada = _respalda_reporte


@app.get("/salud")
def salud():
    return {"estado": "ok", "estrategia_visible": ESTRATEGIA_VISIBLE}


@app.get("/senales")
def catalogo_de_senales():
    """Lista pública de las señales que el motor revisa, para explicar las alertas."""
    return [{"id": s.id, "tipo": s.tipo, "descripcion": s.descripcion} for s in [*CATALOGO, NUMERO_REPORTADO, PATRON_APRENDIDO]]


@app.post("/llamadas", response_model=Llamada, status_code=201)
def crear_llamada(entrada: NuevaLlamada | None = None, sesion: Sesion | None = Depends(sesion_opcional)):
    if len(llamadas) >= MAX_LLAMADAS:
        raise HTTPException(status_code=429, detail="Se alcanzó el máximo de llamadas en memoria")
    llamada = Llamada()
    if entrada and entrada.numero and entrada.numero.strip():
        # Se conserva la reputación y la referencia HMAC del número, no el número
        try:
            rep = reportes.reputacion(entrada.numero)
        except reportes.NumeroInvalido as e:
            raise HTTPException(status_code=422, detail=str(e))
        llamada.numero_reportes, llamada.numero_estado, llamada.numero_ref = rep["reportes"], rep["estado"], rep["ref"]
    if sesion and cuentas.tiene_permiso(sesion.usuario_id, "guardar_historial"):
        llamada.dueno, llamada.guardada = sesion.usuario_id, True
        historial.guardar_llamada(llamada)
    llamadas[llamada.id] = llamada
    return llamada


@app.get("/llamadas/{llamada_id}", response_model=Llamada)
def ver_llamada(llamada_id: str, sesion: Sesion | None = Depends(sesion_opcional)):
    return _buscar(llamada_id, sesion)


@app.post("/llamadas/{llamada_id}/fragmentos")
def agregar_fragmento(llamada_id: str, entrada: FragmentoEntrada, sesion: Sesion | None = Depends(sesion_opcional)):
    return _procesar(_buscar(llamada_id, sesion), entrada)


# Límites del audio (modelo de amenazas, A6)
MAX_AUDIO_BYTES = 10 * 1024 * 1024
TIPOS_AUDIO = ("audio/", "video/webm", "video/mp4", "application/octet-stream")


@app.post("/llamadas/{llamada_id}/audio")
async def agregar_audio(
    llamada_id: str,
    audio: UploadFile = File(...),
    consentimiento: bool = Form(...),
    hablante: str | None = Form(default=None, max_length=50),
    sesion: Sesion | None = Depends(sesion_opcional),
):
    """Transcribe un audio en este equipo y analiza cada segmento como un fragmento.

    El audio se lee en memoria y se descarta al terminar; no se guarda.
    """
    llamada = _buscar(llamada_id, sesion)
    segmentos = await _transcribir_subida(audio, consentimiento)

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


async def _transcribir_subida(audio: UploadFile, consentimiento: bool) -> list:
    """Valida, transcribe en memoria y descarta el audio subido."""
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
        return await run_in_threadpool(whisper.transcribir, datos)
    except whisper.TranscripcionNoDisponible as e:
        raise HTTPException(status_code=503, detail=str(e))
    except whisper.AudioInvalido as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        del datos


# ---- Asistente por voz ----


@app.get("/asistente/comandos")
def comandos_del_asistente():
    return [{"id": c.id, "ejemplo": c.ejemplo} for c in asistente.COMANDOS if c.id != "accion_sensible"]


@app.post("/asistente")
def consultar_asistente(consulta: ConsultaAsistente, sesion: Sesion | None = Depends(sesion_opcional)):
    llamada = _buscar(consulta.llamada_id, sesion) if consulta.llamada_id else None
    r = asistente.responder(consulta.texto, llamada, ESTRATEGIA_VISIBLE)
    log.info("asistente intencion=%s", r.intencion)
    return {"intencion": r.intencion, "respuesta": r.texto, "requiere_confirmacion": r.requiere_confirmacion}


@app.post("/asistente/voz")
async def consultar_asistente_por_voz(
    audio: UploadFile = File(...),
    consentimiento: bool = Form(...),
    llamada_id: str | None = Form(default=None, max_length=64),
    sesion: Sesion | None = Depends(sesion_opcional),
):
    """Transcribe una orden hablada y la responde. El audio no se guarda."""
    llamada = _buscar(llamada_id, sesion) if llamada_id else None
    segmentos = await _transcribir_subida(audio, consentimiento)
    texto = " ".join(s.texto for s in segmentos).strip()[:500]
    if not texto:
        return {"transcripcion": "", "intencion": "desconocido", "requiere_confirmacion": False,
                "respuesta": "No te escuché bien. Intenta de nuevo, más cerca del micrófono."}
    r = asistente.responder(texto, llamada, ESTRATEGIA_VISIBLE)
    log.info("asistente_voz intencion=%s", r.intencion)
    return {"transcripcion": texto, "intencion": r.intencion, "respuesta": r.texto,
            "requiere_confirmacion": r.requiere_confirmacion}


@app.post("/voz")
async def hablar(entrada: TextoParaVoz):
    """Convierte una respuesta en voz con Piper, en este equipo."""
    try:
        wav = await run_in_threadpool(voz.sintetizar, entrada.texto)
    except voz.VozNoDisponible as e:
        raise HTTPException(status_code=503, detail=str(e))
    return Response(content=wav, media_type="audio/wav", headers={"Cache-Control": "no-store"})


def _procesar(llamada: Llamada, entrada: FragmentoEntrada) -> dict:
    if len(llamada.fragmentos) >= MAX_FRAGMENTOS_POR_LLAMADA:
        raise HTTPException(status_code=413, detail="La llamada superó el máximo de fragmentos")

    previas = [f.texto for f in llamada.fragmentos]
    fragmento = Fragmento(**entrada.model_dump())
    # Ambas estrategias deciden sobre el mismo diálogo; el registro guarda las dos
    externas = [NUMERO_REPORTADO] if llamada.numero_estado in reportes.ESTADOS_CON_SENAL else []
    fragmento.decisiones = [e.decidir(previas, entrada.texto, externas) for e in estrategias]
    llamada.fragmentos.append(fragmento)

    visible = next(d for d in fragmento.decisiones if d.estrategia == ESTRATEGIA_VISIBLE)
    mostrar_aviso = visible.alerta and not llamada.aviso_visible
    if mostrar_aviso:
        llamada.aviso_visible = True
    if llamada.guardada:
        historial.guardar_fragmento(llamada, fragmento)

    log.info(
        "llamada=%s fragmento=%s niveles=%s aviso=%s",
        llamada.id,
        fragmento.id,
        ",".join(f"{d.estrategia}:{d.nivel}" for d in fragmento.decisiones),
        mostrar_aviso,
    )
    return {"fragmento": fragmento, "mostrar_aviso": mostrar_aviso, "decision_visible": visible}


def _buscar(llamada_id: str, sesion: Sesion | None) -> Llamada:
    llamada = llamadas.get(llamada_id)
    # Una llamada con dueño solo la ve su dueño; para los demás no existe (modelo de amenazas, A7)
    if llamada is None or (llamada.dueno and (sesion is None or sesion.usuario_id != llamada.dueno)):
        raise HTTPException(status_code=404, detail="Llamada no encontrada")
    return llamada


app.include_router(base_guiones.router)
app.include_router(cuentas.router)
app.include_router(historial.router)
app.include_router(mensajes.router)
app.include_router(reportes.router)
app.include_router(senalizacion.router)


# La interfaz se sirve al final para que las rutas de la API tengan prioridad
app.mount("/", StaticFiles(directory=FRONTEND, html=True), name="interfaz")
