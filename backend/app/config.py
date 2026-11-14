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
    estrategia_visible: Literal["por_fragmento", "acumulacion", "hibrida"] = "hibrida"
    # Modelo del clasificador en JSON; vacío usa el que viene en backend/app/modelo_clasificador.json
    modelo_clasificador: str = ""
    # Modelo de faster-whisper (tiny, base, small...) para correr en CPU
    modelo_whisper: str = "base"
    # Candidatos que compara Whisper por palabra: 5 es más preciso; 1 tarda más o menos la mitad en un portátil lento
    whisper_haz: int = Field(default=5, ge=1, le=10)
    # Leer el modelo de voz al arrancar, para que la primera frase no espere (lo activa sustentacion.py)
    precargar_voz: bool = False
    # Llave de la pantalla del presentador; vacía la apaga (la pone sustentacion.py en cada arranque)
    presentador_llave: str = ""
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

    # Llamada por Centinela entre redes distintas (datos móviles, otro Wi-Fi).
    # STUN descubre la dirección pública de cada celular; TURN retransmite el audio cuando no hay camino directo.
    # Vacío deja la llamada solo para la misma red, como en la beta.
    stun_url: str = ""
    # Un TURN cualquiera con usuario y clave fijos (por ejemplo, el de Metered o uno propio)
    turn_url: str = ""
    turn_usuario: str = ""
    turn_clave: str = ""
    # O el TURN de Cloudflare, que da credenciales temporales a partir de una llave
    cloudflare_turn_llave: str = ""
    cloudflare_turn_token: str = ""


ajustes = Ajustes()
