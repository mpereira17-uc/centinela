import pytest

from app.cuentas import LimitePorCliente


@pytest.fixture(autouse=True)
def limites_limpios():
    """Cada prueba empieza sin solicitudes contadas: todas salen del mismo cliente de pruebas."""
    LimitePorCliente.reiniciar_todos()
    yield
