import json

import httpx
import pytest
from fastapi.testclient import TestClient

from app import instalacion
from app.config import ajustes
from app.main import app

cliente = TestClient(app)
PAGINAS = ("/", "/llamada.html", "/acompanante.html", "/practica.html", "/ayuda.html", "/cuenta.html", "/instalar.html", "/comunidad.html", "/revisar.html")


@pytest.fixture(autouse=True)
def sin_turn(monkeypatch):
    for campo in ("stun_url", "turn_url", "turn_usuario", "turn_clave", "cloudflare_turn_llave", "cloudflare_turn_token"):
        monkeypatch.setattr(ajustes, campo, "")
    instalacion._cache.update(servidores=None, vence=0.0)


# ---- App instalable ----


def test_manifiesto_instalable():
    r = cliente.get("/manifest.webmanifest")
    assert r.status_code == 200
    m = json.loads(r.text)
    assert m["display"] == "standalone" and m["start_url"].startswith("/")
    tamanos = {i["sizes"] for i in m["icons"]}
    assert {"192x192", "512x512"} <= tamanos
    assert any(i["purpose"] == "maskable" for i in m["icons"])
    for icono in m["icons"]:
        assert cliente.get(icono["src"]).headers["content-type"] == "image/png"


def test_todas_las_paginas_enlazan_el_manifiesto():
    for pagina in PAGINAS:
        html = cliente.get(pagina).text
        assert 'rel="manifest" href="/manifest.webmanifest"' in html, pagina
        assert "<script>" not in html and "onclick=" not in html and "style=" not in html, pagina


def test_el_service_worker_no_guarda_la_api():
    r = cliente.get("/sw.js")
    assert r.status_code == 200 and "javascript" in r.headers["content-type"]
    # Solo la interfaz: nada de /llamadas, /reportes, /cuentas ni /historial
    for ruta in ("/llamadas", "/reportes", "/cuentas", "/historial"):
        assert f'"{ruta}' not in r.text
    assert 'ev.request.method !== "GET"' in r.text


def test_qr_lleva_a_la_pagina_de_instalar():
    r = cliente.get("/instalar/qr.svg")
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("image/svg+xml")
    assert r.headers["cache-control"] == "no-store"
    assert r.text.lstrip().startswith(("<?xml", "<svg"))


def test_paginas_nuevas_sin_html_dinamico():
    for js in ("/acompanante.js", "/instalar.js"):
        texto = cliente.get(js).text
        assert "innerHTML" not in texto and "insertAdjacentHTML" not in texto and "document.write" not in texto
        assert "confirm(" not in texto and "alert(" not in texto


# ---- Modo acompañante ----


def test_acompanante_pide_consentimiento_y_explica_el_limite():
    html = cliente.get("/acompanante.html").text
    assert 'id="consentimiento"' in html
    assert "altavoz" in html
    assert "no dejan que ninguna app oiga el audio de una llamada telefónica" in html


def test_acompanante_sin_filtros_que_borren_la_voz_del_altavoz():
    js = cliente.get("/acompanante.js").text
    assert "echoCancellation: false" in js and "noiseSuppression: false" in js


def test_acompanante_usa_el_mismo_analisis_de_audio(monkeypatch):
    from app.transcripcion import whisper
    from app.transcripcion.whisper import Segmento

    monkeypatch.setattr(whisper, "transcribir", lambda datos: [Segmento(texto="Le hablamos del banco, necesito el código que le llegó", inicio=0, fin=4)])
    llamada = cliente.post("/llamadas").json()
    r = cliente.post(
        f"/llamadas/{llamada['id']}/audio",
        files={"audio": ("trozo.mp4", b"x" * 3000, "audio/mp4")},
        data={"consentimiento": "true", "hablante": "altavoz"},
    )
    assert r.status_code == 200
    assert r.json()["resultados"][0]["fragmento"]["hablante"] == "altavoz"


# ---- Llamada entre redes ----


def test_sin_configurar_la_llamada_queda_en_la_misma_red():
    assert cliente.get("/webrtc/ice").json() == {"iceServers": [], "entre_redes": False}


def test_stun_y_turn_propios(monkeypatch):
    monkeypatch.setattr(ajustes, "stun_url", "stun:stun.ejemplo.co:3478")
    monkeypatch.setattr(ajustes, "turn_url", "turn:turn.ejemplo.co:3478")
    monkeypatch.setattr(ajustes, "turn_usuario", "u")
    monkeypatch.setattr(ajustes, "turn_clave", "c")
    datos = cliente.get("/webrtc/ice").json()
    assert datos["entre_redes"] is True
    assert datos["iceServers"] == [
        {"urls": "stun:stun.ejemplo.co:3478"},
        {"urls": "turn:turn.ejemplo.co:3478", "username": "u", "credential": "c"},
    ]


def _cloudflare_falso(monkeypatch, respuesta):
    llamadas = []

    def post(url, headers, json, timeout):
        llamadas.append(url)
        return httpx.Response(200, json=respuesta, request=httpx.Request("POST", url))

    monkeypatch.setattr(instalacion.httpx, "post", post)
    monkeypatch.setattr(ajustes, "cloudflare_turn_llave", "llave")
    monkeypatch.setattr(ajustes, "cloudflare_turn_token", "token")
    return llamadas


def test_turn_de_cloudflare_con_cache(monkeypatch):
    servidor = {"urls": ["turn:turn.cloudflare.com:3478?transport=udp"], "username": "x", "credential": "y"}
    llamadas = _cloudflare_falso(monkeypatch, {"iceServers": [servidor]})
    assert cliente.get("/webrtc/ice").json() == {"iceServers": [servidor], "entre_redes": True}
    cliente.get("/webrtc/ice")
    assert len(llamadas) == 1  # las credenciales se reutilizan mientras duran


def test_turn_de_cloudflare_formato_anterior(monkeypatch):
    servidor = {"urls": ["turn:turn.cloudflare.com:3478"], "username": "x", "credential": "y"}
    _cloudflare_falso(monkeypatch, {"iceServers": servidor})
    assert cliente.get("/webrtc/ice").json()["iceServers"] == [servidor]


def test_si_cloudflare_falla_la_llamada_sigue_en_la_misma_red(monkeypatch):
    def post(*a, **k):
        raise httpx.ConnectError("sin red")

    monkeypatch.setattr(instalacion.httpx, "post", post)
    monkeypatch.setattr(ajustes, "cloudflare_turn_llave", "llave")
    monkeypatch.setattr(ajustes, "cloudflare_turn_token", "token")
    assert cliente.get("/webrtc/ice").json() == {"iceServers": [], "entre_redes": False}


def test_la_llamada_usa_los_servidores_configurados():
    js = cliente.get("/llamada.js").text
    assert 'fetch("/webrtc/ice")' in js
    assert "iceServers: estado.ice" in js


def test_websocket_acepta_el_origen_publico_configurado(monkeypatch):
    from app import senalizacion

    monkeypatch.setattr(ajustes, "origen", "https://demo.trycloudflare.com")
    codigo = cliente.post("/salas").json()["codigo"]
    with cliente.websocket_connect(f"/salas/{codigo}/ws?rol=llama", headers={"origin": "https://demo.trycloudflare.com"}) as ws:
        ws.send_text(json.dumps({"tipo": "unirse", "consentimiento": True}))
        assert json.loads(ws.receive_text())["tipo"] == "unido"
    senalizacion.salas.clear()


# ---- Compartir con Centinela ----


def test_la_app_instalable_recibe_mensajes_compartidos_por_post():
    m = json.loads(cliente.get("/manifest.webmanifest").text)
    destino = m["share_target"]
    # Por POST, para que el mensaje no quede en la dirección ni en los registros del servidor
    assert destino["method"] == "POST" and destino["action"] == "/compartir"
    assert destino["params"]["text"] == "texto"
    sw = cliente.get("/sw.js").text
    assert 'url.pathname !== "/compartir"' in sw and "Response.redirect" in sw


def test_compartir_sin_service_worker_no_lee_el_texto():
    r = cliente.post("/compartir", data={"texto": "Su paquete está retenido"}, follow_redirects=False)
    assert r.status_code == 303
    assert r.headers["location"] == "/?compartido=sin-texto#mensaje"
    assert "paquete" not in r.headers["location"]


def test_la_pagina_explica_como_compartir():
    assert "Compartir y elige Centinela" in cliente.get("/").text


# ---- Voz lista antes de la primera frase ----


class _ModeloFalso:
    def __init__(self):
        self.llamadas = []

    def transcribe(self, audio, **opciones):
        self.llamadas.append(opciones)
        return iter([]), None


@pytest.fixture
def estado_de_voz_limpio():
    from app.transcripcion import whisper

    guardado = dict(whisper._estado)
    yield whisper
    whisper._estado.clear()
    whisper._estado.update(guardado)


def test_el_estado_de_la_voz_no_dice_nada_de_lo_que_se_dijo(estado_de_voz_limpio):
    datos = cliente.get("/transcripcion/estado").json()
    assert set(datos) == {"modelo", "estado", "detalle", "ultima_segundos"}


def test_precargar_deja_la_voz_lista(monkeypatch, estado_de_voz_limpio):
    whisper = estado_de_voz_limpio
    modelo = _ModeloFalso()
    monkeypatch.setattr(whisper, "_modelo", lambda: modelo)
    whisper.precargar()
    assert whisper.estado()["estado"] == "lista"
    assert len(modelo.llamadas) == 1  # una transcripción de prueba para calentar el modelo


def test_precargar_sin_whisper_lo_dice(monkeypatch, estado_de_voz_limpio):
    whisper = estado_de_voz_limpio

    def sin_modelo():
        raise whisper.TranscripcionNoDisponible("Ejecuta: pip install -r requirements-ml.txt")

    monkeypatch.setattr(whisper, "_modelo", sin_modelo)
    whisper.precargar()
    assert whisper.estado()["estado"] == "no_disponible"
    assert "requirements-ml.txt" in cliente.get("/transcripcion/estado").json()["detalle"]


def test_cada_frase_se_transcribe_sola_y_se_mide_cuanto_tarda(monkeypatch, estado_de_voz_limpio):
    whisper = estado_de_voz_limpio
    modelo = _ModeloFalso()
    monkeypatch.setattr(whisper, "_modelo", lambda: modelo)
    whisper.transcribir(b"audio")
    assert modelo.llamadas[0]["condition_on_previous_text"] is False
    assert modelo.llamadas[0]["beam_size"] == ajustes.whisper_haz
    assert isinstance(whisper.estado()["ultima_segundos"], float)


# ---- Escucha por pausas y revisión previa ----


def test_llamada_y_acompanante_escuchan_por_pausas():
    for pagina, script in (("/llamada.html", "/llamada.js"), ("/acompanante.html", "/acompanante.js")):
        html = cliente.get(pagina).text
        assert html.index('src="/escucha.js"') < html.index(f'src="{script}"'), pagina
        assert "CentinelaEscucha.escuchar" in cliente.get(script).text
    js = cliente.get("/escucha.js").text
    assert "innerHTML" not in js and "PAUSA" in js
    # Si no se puede medir el volumen, vuelve a trozos fijos en vez de dejar de escuchar
    assert "modoFijo" in js


def test_la_llamada_aguanta_cortes_de_la_senal():
    js = cliente.get("/llamada.js").text
    assert "llave" in js and '{ tipo: "ping" }' in js and "iceRestart: true" in js


def test_revision_previa_a_la_demo():
    html = cliente.get("/revisar.html").text
    assert 'rel="manifest" href="/manifest.webmanifest"' in html
    assert "<script>" not in html and "onclick=" not in html and "style=" not in html
    js = cliente.get("/revisar.js").text
    assert "innerHTML" not in js and "insertAdjacentHTML" not in js
    # Prueba de verdad que el TURN responde desde la red del celular
    assert '"relay"' in js and "/transcripcion/estado" in js
    assert 'href="/revisar.html"' in cliente.get("/instalar.html").text
    sw = cliente.get("/sw.js").text
    assert '"/revisar.html"' in sw and '"/escucha.js"' in sw and '"/revisar.js"' in sw


def test_sustentacion_usa_stun_publico_si_no_hay_uno(tmp_path, monkeypatch):
    import importlib.util
    from pathlib import Path

    ruta = Path(__file__).resolve().parents[2] / "sustentacion.py"
    spec = importlib.util.spec_from_file_location("sustentacion", ruta)
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    monkeypatch.setattr(modulo, "RAIZ", tmp_path)
    monkeypatch.delenv("CENTINELA_STUN_URL", raising=False)
    (tmp_path / "backend").mkdir()
    assert modulo.configurado_en_env("CENTINELA_STUN_URL") is False
    (tmp_path / "backend" / ".env").write_text("CENTINELA_STUN_URL=stun:propio.co:3478\n", encoding="utf-8")
    assert modulo.configurado_en_env("CENTINELA_STUN_URL") is True
    assert modulo.STUN_PUBLICO.startswith("stun:")
