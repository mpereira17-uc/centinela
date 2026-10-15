from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)


def test_la_raiz_sirve_la_interfaz_en_espanol():
    r = cliente.get("/")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/html")
    assert '<html lang="es">' in r.text
    assert "Analizar frase" in r.text


def test_la_interfaz_carga_sus_archivos():
    assert cliente.get("/app.js").status_code == 200
    assert cliente.get("/estilos.css").status_code == 200


def test_cabeceras_de_seguridad():
    r = cliente.get("/")
    csp = r.headers["content-security-policy"]
    assert "script-src 'self'" in csp
    assert "frame-ancestors 'none'" in csp
    assert r.headers["x-content-type-options"] == "nosniff"
    assert "microphone=(self)" in r.headers["permissions-policy"]


def test_la_interfaz_no_usa_scripts_ni_estilos_en_linea():
    # Necesario para que la política CSP estricta funcione
    html = cliente.get("/").text
    assert "<script>" not in html and "onclick=" not in html and "style=" not in html


def test_el_texto_del_usuario_nunca_se_inserta_como_html():
    js = cliente.get("/app.js").text
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js and "document.write" not in js


def test_la_api_sigue_respondiendo_con_la_interfaz_montada():
    assert cliente.get("/salud").json()["estado"] == "ok"
    assert cliente.get("/senales").status_code == 200


def test_pantalla_de_cuenta_sin_html_dinamico():
    html = cliente.get("/cuenta.html").text
    assert "<script>" not in html and "onclick=" not in html and "style=" not in html
    js = cliente.get("/cuenta.js").text
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js and "document.write" not in js
    # Sin ventanas emergentes: las confirmaciones se hacen con el PIN en pantalla
    assert "confirm(" not in js and "alert(" not in js


def test_la_pagina_principal_enlaza_a_la_cuenta():
    assert 'href="/cuenta.html"' in cliente.get("/").text


def test_pantalla_de_llamada_sin_html_dinamico():
    html = cliente.get("/llamada.html").text
    assert "<script>" not in html and "onclick=" not in html and "style=" not in html
    js = cliente.get("/llamada.js").text
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js and "document.write" not in js
    # Sin servidores STUN o TURN de terceros
    assert "iceServers: []" in js and "stun:" not in js


def test_script_comun_sin_html_dinamico_y_cargado_en_todas_las_pantallas():
    js = cliente.get("/comun.js").text
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js and "document.write" not in js
    for pagina in ("/", "/cuenta.html", "/llamada.html"):
        assert '<script src="/comun.js" defer></script>' in cliente.get(pagina).text


def test_la_denuncia_se_prepara_en_el_equipo_y_apunta_a_canales_oficiales():
    html = cliente.get("/").text
    assert 'id="preparar-denuncia"' in html
    for canal in ("https://adenunciar.policia.gov.co/", "https://caivirtual.policia.gov.co/", 'href="tel:165"', 'href="tel:123"'):
        assert canal in html
    # Centinela no envía la denuncia a terceros: no hay peticiones a otros dominios
    js = cliente.get("/app.js").text
    assert 'fetch("http' not in js and "fetch(`http" not in js


def test_revisar_un_mensaje_esta_en_la_pagina_principal():
    html = cliente.get("/").text
    assert 'id="form-mensaje"' in html and 'id="msj-resultado"' in html
    assert "/mensajes/analizar" in cliente.get("/app.js").text
