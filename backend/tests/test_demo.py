import pytest
from fastapi.testclient import TestClient

from app import demo, reportes
from app.config import ajustes
from app.main import app


@pytest.fixture(autouse=True)
def base_temporal(tmp_path, monkeypatch):
    monkeypatch.setattr(ajustes, "base_datos", str(tmp_path / "demo.db"))
    reportes.limite_consultas.reiniciar()


def consultar(numero):
    return TestClient(app).post("/numeros/consulta", json={"numero": numero}).json()["estado"]


def test_numeros_de_ejemplo_muestran_cada_aviso():
    demo.sembrar()
    assert consultar("300 000 0001") == "estafa_confirmada"
    assert consultar("300 000 0002") == "varios_reportes"
    assert consultar("601 000 0003") == "publicidad"
    assert consultar("300 123 4567") == "sin_reportes"


def test_sembrar_dos_veces_no_duplica():
    primero = demo.sembrar()
    assert demo.sembrar() == primero


def test_quitar_borra_todo_lo_de_ejemplo():
    demo.sembrar()
    assert demo.quitar() == 3
    assert consultar("300 000 0001") == "sin_reportes"


def test_nadie_entra_a_las_cuentas_de_ejemplo():
    demo.sembrar()
    r = TestClient(app).post("/cuenta/entrar", json={"alias": "demo-sustentacion-1", "pin": "482915"}, headers={"X-Centinela": "1"})
    assert r.status_code == 401
