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
    # Ruta al archivo .onnx de una voz de Piper en español; vacío usa la voz del navegador
    voz_piper: str = ""

    # Base de datos local con cuentas, sesiones y consentimientos
    base_datos: str = "centinela.db"
    # Passkeys: el dominio y el origen exactos desde donde se abre la interfaz
    rp_id: str = "localhost"
    origen: str = "http://localhost:8000"
    # Activar cuando la interfaz se sirva por HTTPS
    cookie_segura: bool = False
    duracion_sesion_horas: int = Field(default=12, ge=1, le=168)
    # Días que se conserva el historial antes de borrarse solo
    dias_retencion: int = Field(default=30, ge=1, le=365)


ajustes = Ajustes()
