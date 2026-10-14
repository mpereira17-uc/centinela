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
