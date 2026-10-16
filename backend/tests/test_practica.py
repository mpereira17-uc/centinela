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
    # Niveles, racha e insignias en la pantalla; la estafa de la semana también en el inicio
    assert 'id="niveles"' in html and 'id="racha"' in html and 'id="semana"' in html and 'id="final-insignia"' in html
    assert 'id="semana-inicio"' in cliente.get("/").text


def _de_practica():
    return [g for g in guiones.cargar() if g.particion in practica.PARTICIONES]


def test_cada_llamada_de_practica_cae_en_un_solo_nivel():
    for g in _de_practica():
        niveles_de_g = [n["id"] for n in practica.NIVELES if g.categoria in n["estafas"] + n["normales"]]
        assert len(niveles_de_g) == 1, (g.id, g.categoria, niveles_de_g)


def test_cada_nivel_alcanza_para_diez_rondas_mitad_y_mitad():
    for n in practica.NIVELES:
        del_nivel = [g for g in _de_practica() if g.categoria in n["estafas"] + n["normales"]]
        assert sum(g.es_riesgo for g in del_nivel) >= 5 and sum(not g.es_riesgo for g in del_nivel) >= 5, n["id"]
        # Las estafas del nivel son de su táctica y las normales no son estafas
        assert all(g.es_riesgo == (g.categoria in n["estafas"]) for g in del_nivel)


def test_rondas_de_un_nivel():
    categoria = {g.id: g.categoria for g in guiones.cargar()}
    for n in practica.NIVELES:
        for semilla in range(3):
            rondas = cliente.get("/practica/rondas", params={"nivel": n["id"], "cantidad": 6, "semilla": semilla}).json()
            assert len(rondas) == 6 and sum(r["etiqueta"] == "riesgo" for r in rondas) == 3
            assert all(categoria[r["id"]] in n["estafas"] + n["normales"] for r in rondas)


def test_nivel_desconocido():
    assert cliente.get("/practica/rondas", params={"nivel": "todo"}).status_code == 422


def test_lista_de_niveles_en_orden():
    niveles = cliente.get("/practica/niveles").json()
    assert [n["id"] for n in niveles] == ["premios", "familiar", "urgencia", "autoridad"]
    assert [n["numero"] for n in niveles] == [1, 2, 3, 4]
    assert all(n["nombre"] and n["tactica"] and n["llamadas"] >= 10 for n in niveles)


def test_la_estafa_de_la_semana_cambia_cada_lunes():
    from datetime import date, timedelta
    lunes = date(2026, 10, 12)
    semana = practica.estafa_de_la_semana(lunes)
    assert semana["semana"] == "2026-10-12"
    for dia in range(7):
        assert practica.estafa_de_la_semana(lunes + timedelta(days=dia)) == semana
    siguiente = practica.estafa_de_la_semana(lunes + timedelta(days=7))
    assert siguiente["titulo"] != semana["titulo"] and siguiente["semana"] == "2026-10-19"
    # Recorre todas las modalidades antes de repetir, cada una con su nivel y tres líneas
    vistas = [practica.estafa_de_la_semana(lunes + timedelta(weeks=i)) for i in range(len(practica.SEMANALES))]
    assert len({v["titulo"] for v in vistas}) == len(practica.SEMANALES)
    for v in vistas:
        assert v["nivel"] in practica.NIVEL_POR_ID and len(v["lineas"]) == 3
        assert v["nivel_nombre"] == practica.NIVEL_POR_ID[v["nivel"]]["nombre"]


def test_la_estafa_de_la_semana_por_la_api():
    r = cliente.get("/practica/semana").json()
    assert r["titulo"] and len(r["lineas"]) == 3 and r["nivel"] in practica.NIVEL_POR_ID
