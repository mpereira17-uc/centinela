"""Revisar un mensaje desde una captura de pantalla (OCR local, sin guardar la imagen)."""
import io

import pytest
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)
PIL = pytest.importorskip("PIL")
pytest.importorskip("rapidocr_onnxruntime")


def _captura(renglones, ancho=720):
    from PIL import Image, ImageDraw, ImageFont

    img = Image.new("RGB", (ancho, 80 + 52 * len(renglones)), "#ffffff")
    dibujo = ImageDraw.Draw(img)
    try:
        letra = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 30)
    except OSError:
        try:
            letra = ImageFont.truetype("DejaVuSans.ttf", 30)
        except OSError:
            pytest.skip("no hay una fuente para dibujar la captura de prueba")
    for i, renglon in enumerate(renglones):
        dibujo.text((30, 30 + i * 52), renglon, fill="#111111", font=letra)
    buffer = io.BytesIO()
    img.save(buffer, "PNG")
    return buffer.getvalue()


def _subir(datos, tipo="image/png"):
    return cliente.post("/mensajes/captura", files={"imagen": ("captura.png", datos, tipo)})


def test_lee_la_captura_y_la_analiza_como_un_mensaje():
    r = _subir(_captura(["Su cuenta sera bloqueada.", "Confirme su clave en bit.ly/banco-seguro", "en los proximos 10 minutos."]))
    assert r.status_code == 200
    datos = r.json()
    assert "clave" in datos["texto_leido"].lower()
    assert datos["nivel"] in ("alto", "critico")
    assert any("bit.ly" in e["dominio"] for e in datos["enlaces"])


def test_rechaza_lo_que_no_es_una_imagen():
    assert _subir(b"hola", "text/plain").status_code == 415
    assert _subir(b"esto no es un png").status_code == 422


def test_una_imagen_sin_texto_lo_dice():
    from PIL import Image

    buffer = io.BytesIO()
    Image.new("RGB", (300, 300), "#ffffff").save(buffer, "PNG")
    r = _subir(buffer.getvalue())
    assert r.status_code == 422 and "texto" in r.json()["detail"]


def test_imagen_demasiado_grande():
    assert _subir(b"0" * (6 * 1024 * 1024 + 10)).status_code == 413
