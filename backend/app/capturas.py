"""Revisar un mensaje desde una captura de pantalla, como Scamio (Bitdefender), Norton Genie o Truecaller.

A muchas personas mayores les cuesta copiar el texto de un SMS o de un WhatsApp; tomar una captura es
más fácil. La imagen se lee en memoria con un OCR local (RapidOCR sobre ONNX, sin internet), el texto
pasa por el mismo análisis de mensajes y la imagen se descarta. No se guarda ni se registra.
"""
import io
from functools import lru_cache

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

from .cuentas import LimitePorCliente
from .mensajes import analizar

router = APIRouter(tags=["mensajes"])
# Leer una imagen gasta bastante CPU: menos que revisar texto
limite_capturas = LimitePorCliente(maximo=15, ventana=60)

MAX_BYTES = 6 * 1024 * 1024
TIPOS = ("image/png", "image/jpeg", "image/webp")
# Más que esto ya no es un mensaje: el análisis de mensajes acepta hasta 2000 caracteres
MAX_TEXTO = 2000


class OcrNoDisponible(Exception):
    pass


@lru_cache(maxsize=1)
def _lector():
    try:
        from rapidocr_onnxruntime import RapidOCR
    except ImportError as e:
        raise OcrNoDisponible from e
    return RapidOCR()


def leer_texto(imagen: bytes) -> str:
    """Texto de la imagen, renglón por renglón en orden de lectura."""
    import numpy as np
    from PIL import Image, UnidentifiedImageError

    try:
        with Image.open(io.BytesIO(imagen)) as img:
            img.load()
            # Las capturas de celular son muy altas; más de 2000 px de ancho no mejora la lectura
            if img.width > 2000:
                img = img.resize((2000, round(img.height * 2000 / img.width)))
            matriz = np.array(img.convert("RGB"))
    except (UnidentifiedImageError, OSError, ValueError) as e:
        raise ValueError("imagen_invalida") from e
    resultado, _ = _lector()(matriz)
    if not resultado:
        return ""
    # Cada renglón trae su caja; se ordenan de arriba abajo y de izquierda a derecha
    renglones = sorted(resultado, key=lambda r: (round(r[0][0][1] / 12), r[0][0][0]))
    return "\n".join(r[1] for r in renglones).strip()


@router.post("/mensajes/captura", dependencies=[Depends(limite_capturas)])
async def analizar_captura(imagen: UploadFile = File(...)):
    if (imagen.content_type or "") not in TIPOS:
        raise HTTPException(status_code=415, detail="Sube una captura en PNG, JPG o WebP.")
    datos = await imagen.read(MAX_BYTES + 1)
    await imagen.close()
    if len(datos) > MAX_BYTES:
        raise HTTPException(status_code=413, detail="La imagen supera los 6 MB.")
    try:
        texto = await run_in_threadpool(leer_texto, datos)
    except OcrNoDisponible:
        raise HTTPException(status_code=503, detail="La lectura de capturas no está instalada. Ejecuta: pip install -r requirements-ml.txt") from None
    except ValueError:
        raise HTTPException(status_code=422, detail="No pudimos abrir la imagen. Prueba con otra captura.") from None
    finally:
        del datos
    if not texto:
        raise HTTPException(status_code=422, detail="No encontramos texto en la imagen. Prueba con una captura más nítida.")
    texto = texto[:MAX_TEXTO]
    return {**analizar(texto), "texto_leido": texto}
