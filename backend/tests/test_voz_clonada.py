"""Señal experimental de voz clonada: solo sube el nivel y nunca dice que una voz es real."""
import pytest
from fastapi.testclient import TestClient

from app import main, voz_clonada
from app.estrategias.acumulacion import Acumulacion
from app.senales import CATALOGO, Nivel, calcular_nivel, detectar
from app.transcripcion import whisper
from app.transcripcion.whisper import Segmento
from evaluacion import guiones

cliente = TestClient(main.app)
estrategia = Acumulacion(Nivel.ALTO, 4)


def _nivel(*frases):
    *previas, ultima = frases
    return estrategia.decidir(list(previas), ultima)


def test_familiar_que_pide_plata_llega_a_critico():
    d = _nivel("Abuela, soy yo, su nieto. Tuve un accidente", "Consígneme por favor")
    assert "voz_dudosa" in [s.id for s in d.senales]
    assert d.nivel == "critico"


def test_sin_pedir_nada_no_aparece():
    d = _nivel("Mamá, estoy detenido en la estación", "Ya le explico cuando llegue")
    assert "voz_dudosa" not in [s.id for s in d.senales]
    assert d.nivel == "moderado"


def test_un_banco_que_pide_el_codigo_no_es_voz_dudosa():
    d = _nivel("Le hablamos del banco", "Dígame el código que le llegó")
    assert "voz_dudosa" not in [s.id for s in d.senales]


def test_solo_puede_subir_el_nivel_en_toda_la_base():
    # Con y sin la regla, en cada turno de cada guion: nunca baja
    for g in guiones.cargar():
        vistas = []
        for t in g.turnos:
            vistas += [s for s in detectar(t.texto) if s not in vistas]
            sin = calcular_nivel(vistas)
            con = calcular_nivel(vistas + voz_clonada.por_contexto(vistas))
            assert con >= sin, g.id


def test_ningun_texto_dice_que_la_voz_es_real():
    for s in (voz_clonada.VOZ_DUDOSA, voz_clonada.VOZ_SINTETICA):
        texto = (s.descripcion + s.motivo).lower()
        assert "autentic" not in texto and "es real" not in texto and "verdader" not in texto
    assert "puede equivocarse" in voz_clonada.VOZ_SINTETICA.descripcion
    assert voz_clonada.VOZ_SINTETICA.tipo == "contexto"
    # Son señales derivadas, no reglas de texto del catálogo
    assert not {"voz_dudosa", "voz_sintetica"} & {s.id for s in CATALOGO}


def test_sin_modelo_el_detector_esta_apagado_y_no_decide():
    d = voz_clonada.DetectorAcustico(ruta="")
    assert not d.activo and d.puntaje(b"cualquier cosa") is None and not d.es_sintetica(b"x")
    assert not voz_clonada.DetectorAcustico(ruta="/no/existe.onnx").activo


class _SesionFalsa:
    def __init__(self, valor):
        self.valor = valor

    def get_inputs(self):
        return [type("Entrada", (), {"name": "audio"})()]

    def run(self, _salidas, entradas):
        assert entradas["audio"].ndim == 2
        return [[[1 - self.valor, self.valor]]]


def _detector(monkeypatch, tmp_path, valor):
    modelo = tmp_path / "voz.onnx"
    modelo.write_bytes(b"modelo")
    d = voz_clonada.DetectorAcustico(ruta=str(modelo), umbral=0.9)
    monkeypatch.setattr(d, "_decodificar", lambda datos: [0.0] * 1600)
    monkeypatch.setattr(d, "_sesion", lambda: _SesionFalsa(valor))
    return d


def test_umbral_alto_y_errores_no_marcan(monkeypatch, tmp_path):
    assert _detector(monkeypatch, tmp_path, 0.95).es_sintetica(b"a")
    assert not _detector(monkeypatch, tmp_path, 0.7).es_sintetica(b"a")
    d = _detector(monkeypatch, tmp_path, 0.99)
    monkeypatch.setattr(d, "_decodificar", lambda datos: (_ for _ in ()).throw(ValueError("audio raro")))
    assert d.puntaje(b"a") is None and not d.es_sintetica(b"a")


@pytest.mark.parametrize("valor, esperado", [(0.97, True), (0.2, False)])
def test_el_audio_marcado_agrega_la_senal_a_la_llamada(monkeypatch, tmp_path, valor, esperado):
    monkeypatch.setattr(whisper, "transcribir", lambda datos: [Segmento("Hola, ¿cómo está?", 0.0, 2.0)])
    monkeypatch.setattr(voz_clonada, "detector", _detector(monkeypatch, tmp_path, valor))
    llamada = cliente.post("/llamadas").json()["id"]
    r = cliente.post(f"/llamadas/{llamada}/audio", files={"audio": ("a.wav", b"RIFF" + b"\0" * 50, "audio/wav")},
                     data={"consentimiento": "true"}).json()
    ids = [s["id"] for s in r["resultados"][0]["decision_visible"]["senales"]]
    assert ("voz_sintetica" in ids) is esperado
    # Sola es de contexto: precaución, sin aviso
    assert r["resultados"][0]["decision_visible"]["nivel"] == ("moderado" if esperado else "bajo")
    assert r["resultados"][0]["decision_visible"]["fuente"] == "contenido"
    # Una frase escrita después sigue llevando la señal: no se desmarca
    siguiente = cliente.post(f"/llamadas/{llamada}/fragmentos", json={"texto": "Bien, gracias", "inicio": 3, "fin": 4}).json()
    assert ("voz_sintetica" in [s["id"] for s in siguiente["decision_visible"]["senales"]]) is esperado
