import logging
import sqlite3

import pytest
from fastapi.testclient import TestClient

from app import cuentas, reportes
from app.config import ajustes
from app.main import app

H = {"X-Centinela": "1"}
PIN = "482915"
NUMERO = "300 123 4567"


@pytest.fixture(autouse=True)
def base_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(ajustes, "base_datos", str(tmp_path / "prueba.db"))
    cuentas.limite_credenciales.reiniciar()
    reportes.limite_consultas.reiniciar()


def _persona(alias):
    c = TestClient(app)
    assert c.post("/cuenta/registro", json={"alias": alias, "pin": PIN}, headers=H).status_code == 201
    return c


def _reportar(c, numero=NUMERO, categoria="suplanta_entidad"):
    return c.post("/reportes", json={"numero": numero, "categoria": categoria}, headers=H)


def _consultar(numero=NUMERO):
    return TestClient(app).post("/numeros/consulta", json={"numero": numero}).json()


@pytest.mark.parametrize("texto,esperado", [
    ("300 123 4567", "573001234567"),
    ("+57 300-123-4567", "573001234567"),
    ("0057 3001234567", "573001234567"),
    ("(601) 555 1234", "576015551234"),
    ("+1 415 555 0100", "14155550100"),
])
def test_normaliza_numeros(texto, esperado):
    assert reportes.normalizar_numero(texto) == esperado


@pytest.mark.parametrize("texto", ["123", "abc", "+57 300 123 4567 999 999"])
def test_rechaza_numeros_invalidos(texto):
    with pytest.raises(reportes.NumeroInvalido):
        reportes.normalizar_numero(texto)


def test_reportar_exige_cuenta_y_cabecera():
    assert _reportar(TestClient(app)).status_code == 401
    ana = _persona("ana")
    assert ana.post("/reportes", json={"numero": NUMERO, "categoria": "otro"}).status_code == 403


def test_mismo_numero_en_otro_formato_cuenta_como_uno():
    ana = _persona("ana")
    assert _reportar(ana).status_code == 201
    assert _reportar(ana, "+57 300 123 4567").status_code == 409
    assert _consultar("3001234567")["reportes"] == 1


def test_consulta_separa_reportado_de_confirmado():
    assert _consultar()["estado"] == "sin_reportes"
    _reportar(_persona("ana"))
    r = _consultar()
    assert r["estado"] == "reportado"
    assert "no confirma" in r["mensaje"]
    _reportar(_persona("beto"))
    r = _consultar()
    assert r["reportes"] == 2 and r["estado"] == "varios_reportes"
    assert "confirmado" not in r["estado"]


def test_la_consulta_no_revela_quien_reporto():
    _reportar(_persona("zorrilla77"))
    r = TestClient(app).post("/numeros/consulta", json={"numero": NUMERO})
    assert "zorrilla" not in r.text


def test_el_numero_no_se_guarda_en_claro():
    _reportar(_persona("ana"))
    con = sqlite3.connect(ajustes.base_datos)
    fila = con.execute("SELECT numero_ref, terminacion FROM reportes").fetchone()
    assert "3001234567" not in fila[0] and fila[1] == "4567"
    volcado = "\n".join(con.iterdump())
    assert "3001234567" not in volcado and "573001234567" not in volcado


def test_limite_de_reportes_por_dia():
    ana = _persona("ana")
    for i in range(reportes.MAX_REPORTES_POR_DIA):
        assert _reportar(ana, f"300 000 {i:04d}").status_code == 201
    assert _reportar(ana, "300 999 9999").status_code == 429


def test_categoria_invalida():
    assert _reportar(_persona("ana"), categoria="lo_que_sea").status_code == 422


def test_ver_y_retirar_mis_reportes():
    ana = _persona("ana")
    beto = _persona("beto")
    _reportar(ana)
    [mio] = ana.get("/reportes/mios").json()
    assert mio["terminacion"] == "4567" and mio["categoria"] == "suplanta_entidad"
    assert beto.get("/reportes/mios").json() == []
    assert beto.delete(f"/reportes/{mio['id']}", headers=H).status_code == 404
    assert ana.delete(f"/reportes/{mio['id']}", headers=H).status_code == 200
    assert _consultar()["reportes"] == 0


def test_eliminar_la_cuenta_retira_sus_reportes():
    ana = _persona("ana")
    _reportar(ana)
    ana.post("/cuenta/eliminar", json={"pin": PIN}, headers=H)
    assert _consultar()["reportes"] == 0


def test_exportar_incluye_mis_reportes_sin_el_numero_completo():
    ana = _persona("ana")
    _reportar(ana)
    datos = ana.get("/cuenta/exportar")
    assert datos.json()["reportes"][0]["terminacion"] == "4567"
    assert "3001234567" not in datos.text


def _decisiones(numero, frases):
    c = TestClient(app)
    llamada = c.post("/llamadas", json={"numero": numero}).json()
    resultados = [
        c.post(f"/llamadas/{llamada['id']}/fragmentos", json={"texto": t, "inicio": i, "fin": i + 1}).json()
        for i, t in enumerate(frases)
    ]
    return llamada, [r["decision_visible"] for r in resultados]


def test_un_solo_reporte_no_cambia_el_analisis():
    _reportar(_persona("ana"))
    llamada, [d] = _decisiones(NUMERO, ["Buenas tardes, ¿cómo está?"])
    assert llamada["numero_reportes"] == 1
    assert d["nivel"] == "bajo" and d["fuente"] == "contenido"


def test_la_reputacion_pesa_como_una_senal_mas_y_nunca_decide_sola():
    for alias in ("ana", "beto", "caro"):
        _reportar(_persona(alias))
    _, [sola] = _decisiones(NUMERO, ["Buenas tardes, ¿cómo está?"])
    # Sola llega a moderado, nunca a alerta
    assert sola["nivel"] == "moderado" and sola["alerta"] is False
    assert sola["fuente"] == "contenido_y_reputacion"
    assert any(s["id"] == "numero_reportado" for s in sola["senales"])

    # Con dos indicios del contenido suma tres señales: alto
    frase = "Le hablamos del banco, ganó un premio."
    _, [con_reportes] = _decisiones(NUMERO, [frase])
    _, [sin_numero] = _decisiones(None, [frase])
    assert sin_numero["nivel"] == "moderado"
    assert con_reportes["nivel"] == "alto"


def test_numero_invalido_al_crear_la_llamada():
    assert TestClient(app).post("/llamadas", json={"numero": "12"}).status_code == 422


def test_la_llamada_no_expone_el_numero():
    llamada, _ = _decisiones(NUMERO, ["hola"])
    assert "numero" not in llamada and "3001234567" not in str(llamada)


def test_catalogo_publico_explica_la_senal_de_reputacion():
    ids = [s["id"] for s in TestClient(app).get("/senales").json()]
    assert "numero_reportado" in ids


def test_logs_sin_numero(caplog):
    with caplog.at_level(logging.INFO, logger="centinela"):
        _reportar(_persona("zorrilla77"))
        _consultar()
        _decisiones(NUMERO, ["hola"])
    assert "4567" not in caplog.text and "zorrilla" not in caplog.text
