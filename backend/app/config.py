from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Ajustes(BaseSettings):
    """Configuración del prototipo. Se puede cambiar con variables CENTINELA_*."""

    model_config = SettingsConfigDict(env_prefix="CENTINELA_", env_file=".env")

    # Nivel mínimo que dispara la alerta en ambas estrategias (se fija en validación)
    nivel_alerta: Literal["moderado", "alto", "critico"] = "alto"
    # Número de fragmentos que recuerda la estrategia de acumulación
    limite_contexto: int = Field(default=5, ge=1, le=50)
    # Estrategia cuyo aviso se muestra en la interfaz de demostración
    estrategia_visible: Literal["por_fragmento", "acumulacion"] = "acumulacion"
    # Modelo de faster-whisper (tiny, base, small...) para correr en CPU
    modelo_whisper: str = "base"


ajustes = Ajustes()
