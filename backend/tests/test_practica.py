"""Modo práctica: llamadas de mentira con la explicación de qué las delataba."""
from fastapi.testclient import TestClient

from app import practica
from app.main import app
from evaluacion import guiones

cliente = TestClient(app)


def setup_function():
    practica.limite_practica.reiniciar()


def test_mitad_estafa_mitad_normal():
    for semilla in range(10):
        rondas = cliente.get("/practica/rondas", params={"cantidad": 6, "semilla": semilla}).json()
        assert len(rondas) == 6
        assert sum(r["etiqueta"] == "riesgo" for r in rondas) == 3
        assert len({r["id"] for r in rondas}) == 6


def test_misma_semilla_mismas_llamadas():
    a = cliente.get("/practica/rondas", params={"semilla": 7}).json()
    b = cliente.get("/practica/rondas", params={"semilla": 7}).json()
    assert [r["id"] for r in a] == [r["id"] for r in b]


def test_solo_usa_llamadas_que_no_entrenan_el_modelo():
    particion = {g.id: g.particion for g in guiones.cargar()}
    for semilla in range(5):
        for r in cliente.get("/practica/rondas", params={"cantidad": 10, "semilla": semilla}).json():
            assert particion[r["id"]] in practica.PARTICIONES


def test_cada_estafa_trae_pistas_y_la_frase_trampa():
    for r in cliente.get("/practica/rondas", params={"cantidad": 10, "semilla": 3}).json():
        assert r["turnos"] and r["explicacion"]
        if r["etiqueta"] == "riesgo":
            assert 1 <= len(r["pistas"]) <= 3
            assert r["frase_clave"] == r["turnos"][r["turno_riesgo"]]["texto"]
        else:
            assert r["pistas"] == [] and r["frase_clave"] is None


def test_limita_la_cantidad():
    assert cliente.get("/practica/rondas", params={"cantidad": 50}).status_code == 422


def test_la_pantalla_existe_sin_codigo_en_linea():
    html = cliente.get("/practica.html").text
    assert 'id="ronda"' in html and "/practica.js" in html and "<script>" not in html and "style=" not in html
    assert "innerHTML" not in cliente.get("/practica.js").text
    assert 'href="/practica.html"' in cliente.get("/").text
