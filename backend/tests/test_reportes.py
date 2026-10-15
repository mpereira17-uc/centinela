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


def _persona(alias, nueva=False):
    """Crea una cuenta; salvo que sea nueva, se le da más de un día de antigüedad."""
    c = TestClient(app)
    assert c.post("/cuenta/registro", json={"alias": alias, "pin": PIN}, headers=H).status_code == 201
    if not nueva:
        con = sqlite3.connect(ajustes.base_datos)
        con.execute("UPDATE usuarios SET creado = creado - 2 * 86400 WHERE alias = ?", (alias,))
        con.commit()
        con.close()
    return c


def _reportar(c, numero=NUMERO, categoria="suplanta_entidad", resultado="intento", **extra):
    cuerpo = {"numero": numero, "resultado": resultado, **extra}
    if categoria:
        cuerpo["categoria"] = categoria
    return c.post("/reportes", json=cuerpo, headers=H)


def _envejecer_reportes(dias):
    con = sqlite3.connect(ajustes.base_datos)
    con.execute("UPDATE reportes SET creado = creado - ? * 86400", (dias,))
    con.commit()
    con.close()


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


# ---- Reputación comunitaria: confirmación y protección contra abusos (A22) ----

def test_cuentas_recien_creadas_no_cuentan_todavia():
    for alias in ("nuevo1", "nuevo2", "nuevo3"):
        r = _reportar(_persona(alias, nueva=True))
        assert r.status_code == 201 and r.json()["cuenta_nueva"] is True
    c = _consultar()
    assert c["estado"] == "en_revision" and c["reportes"] == 0 and c["senal"] is False


def test_una_avalancha_en_un_dia_solo_cuenta_tres_reportes():
    for i in range(8):
        _reportar(_persona(f"masa{i}"), resultado="perdida")
    p = reportes._pesar(sqlite3.connect(ajustes.base_datos, factory=_ConFilas), _ref())
    assert p["personas"] == reportes.MAX_QUE_CUENTAN_POR_DIA and p["en_espera"] == 5


def test_estafa_confirmada_exige_personas_que_perdieron_algo():
    for alias in ("persona_a1", "persona_a2", "persona_a3", "persona_a4"):
        _reportar(_persona(alias))
    assert _consultar()["estado"] == "varios_reportes"  # 4 intentos: puntaje alto, sin pérdidas
    _envejecer_reportes(1)
    _reportar(_persona("persona_p1"), resultado="perdida")
    _reportar(_persona("persona_p2"), resultado="perdida")
    c = _consultar()
    assert c["estado"] == "estafa_confirmada" and c["senal"] is True
    assert "2 personas" in c["mensaje"]


def test_publicidad_no_cuenta_como_estafa():
    for alias in ("persona_b1", "persona_b2", "persona_b3"):
        assert _reportar(_persona(alias), categoria=None, resultado="publicidad").status_code == 201
    c = _consultar()
    assert c["estado"] == "publicidad" and c["senal"] is False and c["reportes"] == 0


def test_llamadas_legitimas_ponen_el_numero_en_disputa():
    _reportar(_persona("persona_c1"))
    _reportar(_persona("persona_c2"))
    assert _consultar()["senal"] is True
    _reportar(_persona("persona_c3"), categoria=None, resultado="legitima")
    c = _consultar()
    assert c["estado"] == "en_disputa" and c["senal"] is False


def test_los_reportes_viejos_pesan_menos():
    _reportar(_persona("persona_d1"))
    _reportar(_persona("persona_d2"))
    assert _consultar()["estado"] == "varios_reportes"
    _envejecer_reportes(100)
    assert _consultar()["estado"] == "reportado"


def test_estafa_exige_contar_que_hizo():
    r = _reportar(_persona("persona_e1"), categoria=None, resultado="perdida")
    assert r.status_code == 422


def test_reporte_respaldado_por_una_conversacion_analizada():
    ana = _persona("persona_f1")
    llamada = ana.post("/llamadas", json={"numero": NUMERO}).json()
    for i, t in enumerate(["Le hablamos del banco.", "Dígame el código que le llegó por mensaje."]):
        ana.post(f"/llamadas/{llamada['id']}/fragmentos", json={"texto": t, "inicio": i, "fin": i + 1})
    assert _reportar(ana, llamada_id=llamada["id"]).json()["respaldado"] is True
    # La misma conversación no respalda el reporte de otro número
    otra = _reportar(ana, numero="300 765 4321", llamada_id=llamada["id"]).json()
    assert otra["respaldado"] is False
    # Un respaldado más un intento simple ya pasan el umbral
    _reportar(_persona("persona_f2"))
    assert _consultar()["estado"] == "varios_reportes"


def test_mis_reportes_muestran_lo_que_paso():
    ana = _persona("persona_g1")
    _reportar(ana, categoria=None, resultado="legitima")
    [mio] = ana.get("/reportes/mios").json()
    assert mio["resultado"] == "legitima" and mio["descripcion"] == reportes.RESULTADOS["legitima"]


class _ConFilas(sqlite3.Connection):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.row_factory = sqlite3.Row


def _ref():
    return reportes.referencia(NUMERO)
