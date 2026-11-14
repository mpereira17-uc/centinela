"""Avisos escalonados durante la llamada: banner arriba que no tapa la llamada, como Pixel y Samsung.

Precaución sin sonido; riesgo alto y crítico piden "Colgar y verificar" o "No es estafa".
Solo se avisa cuando el nivel sube, y la pantalla completa queda para después de colgar.
"""
import re

from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)
PAGINAS_CON_AVISO = ("/", "/llamada.html", "/acompanante.html")


def test_las_tres_pantallas_tienen_el_mismo_aviso():
    for pagina in PAGINAS_CON_AVISO:
        html = cliente.get(pagina).text
        i = html.index('id="alerta"')
        aviso = html[i:html.index("</section>", i)]
        assert 'class="alerta-decision oculto"' in aviso, pagina
        assert ">Colgar y verificar<" in aviso and ">No es estafa<" in aviso, pagina
        # "Entendido" cierra la precaución, que no pide decidir
        assert 'id="cerrar-alerta"' in aviso, pagina
        assert "Buscar el canal oficial" in aviso, pagina


def test_solo_avisa_cuando_el_nivel_sube():
    js = cliente.get("/comun.js").text
    assert "function escalo(decision)" in js and "n <= escalon" in js
    # Los avisos fuertes piden decidir; la precaución no
    assert 'const fuerte = ["alto", "critico"].includes(decision.nivel)' in js
    # "No es estafa" calla hasta el nivel alto, pero un crítico posterior sí avisa
    assert 'escalon = Math.max(escalon, ORDEN_NIVEL.indexOf("alto"))' in js
    # Vibración solo en alto y crítico, más larga en crítico
    vib = re.search(r"const VIBRACION = \{([^}]*)\}", js).group(1)
    assert "alto" in vib and "critico" in vib and "moderado" not in vib
    for pagina in ("/app.js", "/llamada.js", "/acompanante.js"):
        assert "Centinela?.escalo(" in cliente.get(pagina).text, pagina


def test_un_aviso_fuerte_no_se_cierra_con_un_gesto():
    js = cliente.get("/comun.js").text
    assert 'if (!alerta.classList.contains("pide-decision")) cerrar.click();' in js


def test_el_banner_no_tapa_la_pantalla_y_el_resumen_si():
    css = cliente.get("/estilos.css").text
    bloque = css[css.index("/* ---------- Aviso escalonado"):]
    assert ".alerta {" in bloque and "top:" in bloque.split(".alerta {", 1)[1].split("}", 1)[0]
    assert ".alerta.verificando {" in bloque and "inset: 0" in bloque.split(".alerta.verificando {", 1)[1].split("}", 1)[0]


def test_colgar_desde_el_aviso_termina_la_llamada_por_centinela():
    assert '"centinela:decision"' in cliente.get("/llamada.js").text
    assert '"centinela:decision"' in cliente.get("/acompanante.js").text


def test_la_interfaz_se_revalida_en_cada_carga():
    # Sin esto el navegador puede mezclar un comun.js viejo con un app.js nuevo
    for ruta in ("/", "/comun.js", "/app.js", "/estilos.css", "/llamada.html"):
        assert cliente.get(ruta).headers.get("cache-control") == "no-cache", ruta
    assert cliente.get("/salud").headers.get("cache-control") != "no-cache"
