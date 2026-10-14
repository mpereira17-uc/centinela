import io
import json
import math
import wave

import pytest

from app.transcripcion.whisper import Segmento
from evaluacion import evaluar, generar_audio, guiones
from evaluacion.metricas import mediana, normalizar, wer, wilson


def test_los_guiones_son_validos_y_balanceados():
    todos = guiones.cargar()
    assert len(todos) >= 30
    for particion in guiones.PARTICIONES:
        parte = [g for g in todos if g.particion == particion]
        assert {g.etiqueta for g in parte} == {"riesgo", "legitima"}
    riesgo = sum(g.es_riesgo for g in todos)
    assert riesgo == len(todos) - riesgo


def test_valida_turno_de_riesgo(tmp_path):
    malo = [{"id": "x", "etiqueta": "riesgo", "particion": "desarrollo", "turno_riesgo": 1,
             "turnos": [["llamante", "hola"], ["usuario", "dígame"]]}]
    ruta = tmp_path / "g.json"
    ruta.write_text(json.dumps(malo), encoding="utf-8")
    with pytest.raises(guiones.GuionInvalido):
        guiones.cargar(ruta)


def test_wer():
    assert wer("Dicte el código, por favor", "dicte el codigo por favor") == (0, 5)
    assert wer("me dicta el código", "me dice el código ya") == (2, 4)
    assert wer("hola", "") == (1, 1)
    assert normalizar("¡Él dijo: CÓDIGO!") == ["el", "dijo", "codigo"]


def test_wilson_y_mediana():
    bajo, alto = wilson(9, 10)
    assert 0.55 < bajo < 0.6 and math.isclose(alto, 0.982, abs_tol=0.01)
    assert wilson(0, 0) is None
    assert mediana([3, 1, 2]) == 2 and mediana([1, 2, 3, 4]) == 2.5 and mediana([]) is None


def test_evaluacion_en_texto():
    res = evaluar.evaluar(guiones.cargar())
    assert set(res["resumen"]) == {"por_fragmento", "acumulacion"}
    for r in res["resumen"].values():
        assert r["llamadas_riesgo"] == r["llamadas_legitimas"] == 18
        assert 0 <= r["deteccion"] <= 1
        assert r["segundos_hasta_aviso_mediana"] > 0
    # Un guion claro siempre se detecta y una llamada familiar nunca alerta
    filas = {f["id"]: f for f in res["por_guion"]}
    assert filas["r01"]["estrategias"]["acumulacion"]["alerta"]
    assert not filas["l04"]["estrategias"]["acumulacion"]["alerta"]
    md = evaluar.informe(res, "todas")
    assert "| acumulacion |" in md and "IC 95 %" in md


def _wav_falso(texto, voz):
    # Un tono de 0,1 s por palabra en lugar de la voz de Piper
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(16000)
        w.writeframes(b"\x01\x00" * 1600 * len(texto.split()))
    return buffer.getvalue()


def test_modo_audio_de_punta_a_punta_con_voz_y_transcripcion_simuladas(tmp_path):
    lista = [g for g in guiones.cargar() if g.id in ("r01", "l01")]
    voces = {"llamante": "a.onnx", "usuario": "b.onnx"}
    for g in lista:
        meta = generar_audio.generar(g, voces, _wav_falso, tmp_path)
        assert len(meta["turnos"]) == len(g.turnos)
        assert meta["turnos"][1]["inicio"] > meta["turnos"][0]["fin"]

    # Transcriptor simulado que "oye" los turnos de quien llama en orden, con un error en el primero
    oidos = [t.texto for g in lista for t in g.turnos if t.hablante == "llamante"]
    oidos[0] = oidos[0].replace("titular", "tutelar")

    def transcribir(audio):
        return [Segmento(oidos.pop(0), 0, 1)]

    res = evaluar.evaluar(lista, "audio", carpeta_audio=tmp_path, transcribir=transcribir)
    assert 0 < res["wer"] < 0.05
    assert set(res["wer_por_voz"]) == {"a.onnx"}
    assert "Voz de quien llama" in evaluar.informe(res, "prueba")
    filas = {f["id"]: f for f in res["por_guion"]}
    assert filas["r01"]["estrategias"]["acumulacion"]["alerta"]
    assert "transcripciones" in filas["r01"]
    assert not filas["l01"]["estrategias"]["acumulacion"]["alerta"]
