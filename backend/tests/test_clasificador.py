import pytest
from fastapi.testclient import TestClient

from app import clasificador
from app.analisis import ESTRATEGIA_VISIBLE
from app.main import app
from app.senales import Nivel
from evaluacion import entrenar, guiones

modelo = clasificador.cargar()


def test_el_modelo_entrenado_viene_con_el_repositorio():
    assert modelo is not None
    assert 0.3 <= modelo.umbral <= 0.9
    assert ESTRATEGIA_VISIBLE == "hibrida"


@pytest.mark.parametrize("frase,riesgo", [
    ("Me puede leer los dígitos que le entraron por mensaje", True),
    ("Hágame el favor y me consigna a esta cuenta", True),
    ("Hola, te llamo para el almuerzo del domingo", False),
    ("Le hablamos del banco, su tarjeta está lista en la oficina", False),
])
def test_frases_nuevas(frase, riesgo):
    assert (modelo.probabilidad(frase) >= modelo.umbral) is riesgo


def test_la_hibrida_suma_el_clasificador_sin_quitar_reglas():
    hibrida = clasificador.Hibrida(Nivel.ALTO, 5, modelo)
    evasiva = hibrida.decidir([], "Me puede leer los dígitos que le entraron por mensaje")
    assert evasiva.alerta and [s.id for s in evasiva.senales] == ["patron_aprendido"]
    clara = hibrida.decidir([], "Dígame el código que le llegó, es urgente")
    ids = {s.id for s in clara.senales}
    assert {"pide_codigo", "urgencia"} <= ids and clara.nivel == "critico"
    legitima = hibrida.decidir([], "Le recordamos que su cita es mañana")
    assert not legitima.alerta and legitima.senales == []


def test_sin_modelo_no_hay_hibrida(tmp_path):
    assert clasificador.cargar(str(tmp_path / "no-existe.json")) is None


def test_la_api_usa_la_hibrida_y_explica_la_senal():
    c = TestClient(app)
    assert c.get("/salud").json()["estrategia_visible"] == "hibrida"
    assert "patron_aprendido" in [s["id"] for s in c.get("/senales").json()]
    llamada = c.post("/llamadas").json()
    r = c.post(f"/llamadas/{llamada['id']}/fragmentos",
               json={"texto": "Me puede leer los dígitos que le entraron por mensaje", "inicio": 0, "fin": 3}).json()
    assert r["decision_visible"]["estrategia"] == "hibrida"
    assert r["mostrar_aviso"] is True
    assert "se parece a estafas conocidas" in r["decision_visible"]["mensaje"]


def test_el_entrenamiento_no_usa_guiones_reservados():
    textos, _ = entrenar.ejemplos()
    reservados = {t.texto for g in guiones.cargar(particion="reservada") for t in g.turnos}
    assert not reservados & set(textos)


def test_la_inferencia_sin_scikit_learn_coincide_con_scikit_learn():
    pytest.importorskip("sklearn")
    textos, etiquetas = entrenar.ejemplos()
    vec = entrenar._vectorizador()
    reg = entrenar._regresion().fit(vec.fit_transform(textos), etiquetas)
    propio = clasificador.Modelo({
        "vocabulario": vec.vocabulary_, "idf": list(vec.idf_), "coef": list(reg.coef_[0]),
        "intercepto": float(reg.intercept_[0]), "umbral": 0.5,
    })
    prueba = ["Dígame el código", "Hola mamá", "zzz", "Consigne ya a la cuenta que le digo"]
    for texto, esperado in zip(prueba, reg.predict_proba(vec.transform(prueba))[:, 1]):
        assert propio.probabilidad(texto) == pytest.approx(esperado, abs=1e-9)
