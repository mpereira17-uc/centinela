from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, Field, model_validator

# Límites de entrada para evitar abusos (modelo de amenazas, A6)
MAX_TEXTO = 2000
MAX_FRAGMENTOS_POR_LLAMADA = 500

NivelRiesgo = Literal["bajo", "moderado", "alto", "critico"]


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class FragmentoEntrada(BaseModel):
    """Texto de un fragmento de la llamada con sus marcas de tiempo (segundos)."""

    texto: str = Field(min_length=1, max_length=MAX_TEXTO)
    inicio: float = Field(ge=0)
    fin: float = Field(ge=0)
    hablante: str | None = Field(default=None, max_length=50)

    @model_validator(mode="after")
    def _fin_despues_de_inicio(self):
        if self.fin < self.inicio:
            raise ValueError("fin debe ser mayor o igual que inicio")
        return self


class SenalDetectada(BaseModel):
    id: str
    tipo: str
    descripcion: str


class Decision(BaseModel):
    estrategia: str
    nivel: NivelRiesgo
    alerta: bool
    mensaje: str
    senales: list[SenalDetectada]
    # De dónde sale la sospecha: del contenido, o del contenido más los reportes del número.
    # Nunca es una identidad confirmada.
    fuente: Literal["contenido", "contenido_y_reputacion"] = "contenido"


class Fragmento(FragmentoEntrada):
    id: str = Field(default_factory=lambda: uuid4().hex)
    recibido: datetime = Field(default_factory=_ahora)
    decisiones: list[Decision] = []


class Llamada(BaseModel):
    id: str = Field(default_factory=lambda: uuid4().hex)
    creada: datetime = Field(default_factory=_ahora)
    fragmentos: list[Fragmento] = []
    # Una vez se muestra el aviso no se repite, aunque el transcriptor corrija
    aviso_visible: bool = False
    # Solo se guarda si la persona entró a su cuenta y permitió guardar el historial
    guardada: bool = False
    dueno: str | None = Field(default=None, exclude=True)
    # Personas distintas que reportaron el número que llama; el número en sí no se guarda aquí
    numero_reportes: int = 0


class NuevaLlamada(BaseModel):
    numero: str | None = Field(default=None, max_length=25)


class ConsultaAsistente(BaseModel):
    texto: str = Field(min_length=1, max_length=500)
    llamada_id: str | None = Field(default=None, max_length=64)


class TextoParaVoz(BaseModel):
    texto: str = Field(min_length=1, max_length=1000)
