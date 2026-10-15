"""Directorio de canales oficiales para verificar una llamada o un mensaje."""
import re
from urllib.parse import urlsplit

from fastapi.testclient import TestClient

from app import directorio, enlaces
from app.main import app

cliente = TestClient(app)


def test_responde_agrupado_y_con_consejo_para_bancos():
    datos = cliente.get("/directorio").json()
    tipos = [g["tipo"] for g in datos["grupos"]]
    assert tipos[0] == "emergencia"
    bancos = next(g for g in datos["grupos"] if g["tipo"] == "banco")
    assert "respaldo de tu tarjeta" in bancos["consejo"]


def test_las_lineas_de_emergencia_estan():
    telefonos = {e.get("telefono") for e in directorio.cargar()["entradas"]}
    assert {"123", "165", "122"} <= telefonos


def test_cada_pagina_es_oficial_y_https():
    # Así el directorio y la revisión de enlaces no se contradicen
    for e in directorio.cargar()["entradas"]:
        if "web" in e:
            assert e["web"].startswith("https://"), e["nombre"]
            assert enlaces.revisar(e["web"]).oficial, e["web"]


def test_los_bancos_no_tienen_telefono_inventado():
    # Los números de los bancos cambian y hay muchos falsos en internet: se usa el de la tarjeta o la app
    for e in directorio.cargar()["entradas"]:
        if e["tipo"] in ("banco", "billetera"):
            assert "telefono" not in e
        if "telefono" in e:
            assert re.fullmatch(r"\d{3}", e["telefono"])


def test_la_pantalla_de_ayuda_existe_y_esta_en_la_barra():
    html = cliente.get("/ayuda.html").text
    assert 'id="directorio"' in html and "/ayuda.js" in html and "<script>" not in html and "style=" not in html
    js = cliente.get("/ayuda.js").text
    assert "innerHTML" not in js
    for pagina in ("/", "/cuenta.html", "/llamada.html", "/ayuda.html"):
        assert 'href="/ayuda.html"' in cliente.get(pagina).text


def test_la_guia_me_estafaron_cubre_cada_situacion():
    html = cliente.get("/ayuda.html").text
    js = cliente.get("/ayuda.js").text
    situaciones = ["codigo", "whatsapp", "tarjeta", "transferencia", "aplicacion", "datos", "amenaza"]
    for s in situaciones:
        assert f'value="{s}"' in html
        assert f'"{s}"' in js
    assert "tel:165" in js and "/#denuncia" in js
    assert 'href="/ayuda.html#me-estafaron"' in cliente.get("/").text


def test_palabra_clave_familiar_nunca_pide_la_palabra():
    html = cliente.get("/ayuda.html").text
    assert 'id="palabra-acordada"' in html and 'type="checkbox" id="palabra-acordada"' in html
    i = html.index('id="palabra-clave"')
    seccion = html[i:html.index("</section>", i)]
    assert 'type="text"' not in seccion and "<input" in seccion and seccion.count("<input") == 1
    comun = cliente.get("/comun.js").text
    assert "consejoFamiliar" in comun and "emergencia_familiar" in comun
    for pagina, js in (("/", "/app.js"), ("/llamada.html", "/llamada.js")):
        assert 'class="alerta-clave' in cliente.get(pagina).text
        assert "consejoFamiliar" in cliente.get(js).text
