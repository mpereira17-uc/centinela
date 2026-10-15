"""Estrategias activas y la que se muestra en la interfaz."""
import logging

from .clasificador import Hibrida, RUTA_MODELO, cargar
from .config import ajustes
from .estrategias import Acumulacion, PorFragmento
from .senales import Nivel

log = logging.getLogger("centinela")

_nivel_alerta = Nivel[ajustes.nivel_alerta.upper()]
modelo = cargar(ajustes.modelo_clasificador or str(RUTA_MODELO))

estrategias = [
    PorFragmento(_nivel_alerta),
    Acumulacion(_nivel_alerta, ajustes.limite_contexto),
]
if modelo:
    estrategias.append(Hibrida(_nivel_alerta, ajustes.limite_contexto, modelo))

ESTRATEGIA_VISIBLE = ajustes.estrategia_visible
if ESTRATEGIA_VISIBLE not in {e.nombre for e in estrategias}:
    # Sin modelo entrenado la híbrida no existe; se muestra la acumulación de reglas
    log.warning("No hay modelo del clasificador; la estrategia visible pasa a acumulacion")
    ESTRATEGIA_VISIBLE = "acumulacion"
