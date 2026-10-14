from pydantic_settings import BaseSettings, SettingsConfigDict


class Ajustes(BaseSettings):
    """Configuración del prototipo. Se puede cambiar con variables CENTINELA_*."""

    model_config = SettingsConfigDict(env_prefix="CENTINELA_", env_file=".env")

    # Umbral común para ambas estrategias (se fija en validación, Fase 2)
    umbral: float = 0.6
    # Número de fragmentos que recuerda la estrategia de acumulación
    limite_contexto: int = 5
    # Estrategia cuyo aviso se muestra en la interfaz de demostración
    estrategia_visible: str = "acumulacion"
    # Modelo de faster-whisper (tiny, base, small...) para correr en CPU
    modelo_whisper: str = "base"


ajustes = Ajustes()
