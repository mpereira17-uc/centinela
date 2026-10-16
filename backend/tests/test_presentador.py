"""Pantalla del presentador, cifras automáticas, tarjetas de estafador, aviso hablado y resumen al colgar."""
import csv
import io

import pytest
from fastapi.testclient import TestClient

from app import presentador
from app.analisis import estrategias
from app.config import ajustes
from app.main import app

cliente = TestClient(app)
LLAVE = "llave-de-prueba"
PIDE_CODIGO = "Le hablamos del banco. Dícteme ya el código que le llegó por mensaje o le bloqueamos la cuenta"


@pytest.fixture(autouse=True)
def base_limpia(tmp_path, monkeypatch):
    monkeypatch.setattr(ajustes, "base_datos", str(tmp_path / "prueba.db"))
    monkeypatch.setattr(ajustes, "presentador_llave", "")
    presentador._eventos.clear()
    yield
    presentador._eventos.clear()


def _encender(monkeypatch):
    monkeypatch.setattr(ajustes, "presentador_llave", LLAVE)


def _frase(llamada_id, texto, inicio=0.0, fin=4.0):
    r = cliente.post(f"/llamadas/{llamada_id}/fragmentos", json={"texto": texto, "inicio": inicio, "fin": fin})
    assert r.status_code == 200
    return r.json()


def _eventos(llave=LLAVE, desde=0):
    return cliente.get(f"/presentador/eventos?desde={desde}", headers={"X-Presentador": llave})


# ---- Pantalla del presentador ----


def test_apagada_por_defecto_y_sin_llave_no_se_ve_nada():
    assert cliente.get("/presentador/estado").json() == {"activo": False}
    assert _eventos().status_code == 403


def test_muestra_solo_las_llamadas_marcadas_con_las_tres_estrategias(monkeypatch):
    _encender(monkeypatch)
    assert cliente.get("/presentador/estado").json() == {"activo": True}
    marcada = cliente.post("/llamadas", json={"proyectar": True, "modo": "acompanante"}).json()
    otra = cliente.post("/llamadas", json={}).json()
    _frase(otra["id"], "Esta frase no se debe ver en el video beam")
    _frase(marcada["id"], "Buenas tardes, ¿hablo con el titular?")
    _frase(marcada["id"], PIDE_CODIGO, 4, 9)

    datos = _eventos().json()
    tipos = [e["tipo"] for e in datos["eventos"]]
    assert tipos == ["inicio", "frase", "frase"]
    assert datos["eventos"][0]["modo"] == "acompanante"
    assert all("no se debe ver" not in str(e) for e in datos["eventos"])
    ultima = datos["eventos"][-1]
    assert ultima["frase"] == 2 and ultima["segundo"] == 9.0 and ultima["respuesta"] >= 0
    assert {d["estrategia"] for d in ultima["decisiones"]} == {e.nombre for e in estrategias}
    assert any(d["alerta"] for d in ultima["decisiones"])
    # Solo llegan los eventos nuevos
    assert _eventos(desde=ultima["n"]).json()["eventos"] == []


def test_llave_equivocada_y_limpiar(monkeypatch):
    _encender(monkeypatch)
    cliente.post("/llamadas", json={"proyectar": True})
    assert _eventos("otra").status_code == 403
    assert cliente.delete("/presentador/eventos", headers={"X-Presentador": LLAVE}).status_code == 204
    assert _eventos().json()["eventos"] == []


def test_sin_pantalla_activa_la_casilla_no_proyecta():
    llamada = cliente.post("/llamadas", json={"proyectar": True}).json()
    _frase(llamada["id"], PIDE_CODIGO)
    assert list(presentador._eventos) == []


def test_el_desenlace_se_ve_en_la_pantalla(monkeypatch):
    _encender(monkeypatch)
    llamada = cliente.post("/llamadas", json={"proyectar": True}).json()
    _frase(llamada["id"], PIDE_CODIGO)
    cliente.post(f"/llamadas/{llamada['id']}/desenlace", json={"resultado": "intento"})
    assert _eventos().json()["eventos"][-1] == {**_eventos().json()["eventos"][-1], "tipo": "desenlace", "resultado": "intento"}


# ---- Cifras automáticas ----


def test_cifras_por_estrategia_sin_texto(monkeypatch):
    estafa = cliente.post("/llamadas", json={}).json()
    _frase(estafa["id"], "Buenas tardes, ¿hablo con el titular?", 0, 3)
    _frase(estafa["id"], PIDE_CODIGO, 3, 8)
    cliente.post(f"/llamadas/{estafa['id']}/desenlace", json={"resultado": "intento"})
    normal = cliente.post("/llamadas", json={}).json()
    _frase(normal["id"], "Hola mami, ya voy llegando a la casa, ¿quieres que compre pan?")
    cliente.post(f"/llamadas/{normal['id']}/desenlace", json={"resultado": "legitima"})

    r = cliente.get("/metricas/resumen").json()
    assert r["llamadas"] == 2 and r["con_desenlace"] == 2
    assert set(r["por_estrategia"]) == {e.nombre for e in estrategias}
    for v in r["por_estrategia"].values():
        assert v["llamadas_con_aviso"] == 1 and v["frase_media_del_aviso"] == 2 and v["segundo_medio_del_aviso"] == 8
        assert v["estafas_avisadas"] == 1 and v["falsas_alarmas"] == 0 and v["normales_sin_aviso"] == 1
    assert r["respuesta_media_segundos"] is not None


def test_el_csv_pide_la_llave_y_no_lleva_lo_que_se_dijo(monkeypatch):
    llamada = cliente.post("/llamadas", json={}).json()
    _frase(llamada["id"], PIDE_CODIGO)
    assert cliente.get("/metricas.csv").status_code == 403
    _encender(monkeypatch)
    r = cliente.get("/metricas.csv", headers={"X-Presentador": LLAVE})
    assert r.status_code == 200 and r.headers["content-type"].startswith("text/csv")
    filas = list(csv.reader(io.StringIO(r.text)))
    assert filas[0][:4] == ["fecha", "origen", "proyectada", "frases"]
    assert "acumulacion_frase_aviso" in filas[0]
    assert len(filas) == 2 and filas[1][1] == "texto"
    assert "código" not in r.text and llamada["id"] not in r.text


# ---- Tarjetas de estafador ----


def test_tarjeta_al_azar():
    g = cliente.get("/guiones/al-azar?etiqueta=riesgo").json()
    assert g["etiqueta"] == "riesgo" and g["turnos"] and g["descripcion"]
    assert cliente.get("/guiones/al-azar?etiqueta=otra").status_code == 422
    html = cliente.get("/tarjetas.html").text
    assert 'src="/tarjetas.js"' in html and "<script>" not in html and "style=" not in html
    js = cliente.get("/tarjetas.js").text
    assert "innerHTML" not in js and "/guiones/al-azar" in js


# ---- Páginas ----


def test_pantalla_del_presentador_sin_html_dinamico_y_sin_llave_a_la_vista():
    html = cliente.get("/presentador.html").text
    assert "<script>" not in html and "style=" not in html and 'src="/presentador.js"' in html
    js = cliente.get("/presentador.js").text
    assert "innerHTML" not in js and "X-Presentador" in js
    # La llave se quita de la dirección para que no quede proyectada
    assert "history.replaceState" in js


def test_aviso_hablado_y_resumen_en_las_dos_pantallas_de_llamada():
    comun = cliente.get("/comun.js").text
    assert "decirAviso" in comun and "pintarResumen" in comun and '"decir"' in comun
    assert "innerHTML" not in comun
    for pagina, script in (("/llamada.html", "/llamada.js"), ("/acompanante.html", "/acompanante.js")):
        html = cliente.get(pagina).text
        assert 'id="aviso-voz"' in html and 'id="resumen"' in html and 'id="caja-proyectar"' in html, pagina
        js = cliente.get(script).text
        assert "decirAviso(d)" in js and "pintarResumen" in js, script
    # En el modo acompañante el micrófono oiría el aviso: mientras lo dice, deja de escuchar
    assert "silenciar(ms)" in cliente.get("/acompanante.js").text and "silenciar(ms)" in cliente.get("/escucha.js").text
