from datetime import datetime, timezone
from uuid import uuid4

from pydantic import BaseModel, Field


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


class FragmentoEntrada(BaseModel):
    """Texto de un fragmento de la llamada con sus marcas de tiempo (segundos)."""

    texto: str
    inicio: float = Field(ge=0)
    fin: float = Field(ge=0)
    hablante: str | None = None


class Decision(BaseModel):
    estrategia: str
    puntaje: float
    alerta: bool
    indicios: list[str]


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
