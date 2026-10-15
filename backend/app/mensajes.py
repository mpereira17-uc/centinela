"""Análisis de un mensaje que la persona recibió (SMS, WhatsApp o correo).

Usa el mismo motor de señales que las llamadas y le suma la revisión de los enlaces.
El mensaje no se guarda ni se registra en los logs.
"""
import re
from dataclasses import replace

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from . import enlaces
from .cuentas import LimitePorCliente
from .senales import Nivel, Senal, Tipo, calcular_nivel, detectar, mensaje, _p

router = APIRouter(tags=["mensajes"])
limite_mensajes = LimitePorCliente(maximo=30, ventana=60)

ENLACE_SUPLANTA = Senal(
    "enlace_suplanta", Tipo.SOLICITUD,
    "El mensaje trae un enlace que usa el nombre de una entidad pero no es su página oficial.",
    "el enlace imita a una entidad pero no es su página oficial", _p(r"(?!)"),
)
ENLACE_SOSPECHOSO = Senal(
    "enlace_sospechoso", Tipo.CONTEXTO,
    "El mensaje trae un enlace acortado, numérico o con una terminación muy usada en engaños.",
    "el enlace esconde a dónde lleva", _p(r"(?!)"),
)
PIDE_ENTRAR = Senal(
    "pide_entrar_enlace", Tipo.SOLICITUD,
    "Pide entrar a un enlace que no es oficial para pagar, actualizar datos o reclamar algo.",
    "te piden entrar a un enlace para pagar o dar tus datos",
    _p(r"\b(ingres\w*|entr[ea]\w*|haga clic|de clic|dar clic|click|clic|pagu?e\w*|actualic\w*|reclam\w*|verifiq\w*|confirm\w*|descargu?e\w*)\b"),
)
CATALOGO_MENSAJES = [ENLACE_SUPLANTA, ENLACE_SOSPECHOSO, PIDE_ENTRAR]

# Qué hacer con un mensaje; en una llamada se dice "cuelga", aquí no aplica
ACCIONES = {
    Nivel.BAJO: "No encontramos señales de estafa en este mensaje. Esto no garantiza que sea seguro.",
    Nivel.MODERADO: "No respondas con datos personales ni bancarios. Si dudas, consulta a la entidad por su aplicación o su número oficial.",
    Nivel.ALTO: "No entres al enlace ni respondas. Verifica con la entidad por su aplicación o su número oficial.",
    Nivel.CRITICO: "No entres al enlace, no envíes dinero ni códigos. Bloquea el número y contacta a tu banco por su canal oficial.",
}


class MensajeEntrada(BaseModel):
    texto: str = Field(min_length=1, max_length=2000)


# Motivos dichos para un mensaje escrito, no para una llamada
_MOTIVOS = {"suplanta_entidad": "dicen ser de una entidad", "aislamiento": "te piden no contarle a nadie"}
# Un mensaje que trae el código ("su clave dinámica es 123456") lo entrega, no lo pide
_ENTREGA_CODIGO = re.compile(r"\b(codigo|clave|token|otp|pin)\b[^.]{0,40}?\b(es|:)\s*\d{4,8}\b")
_REENVIAR = re.compile(r"\b(envie\w*|reenvie\w*|mande(la|lo|nos)?|dictel[ao]|respond\w* (con|este)|escrib\w* (aqui|en este))\b")
# En un mensaje, que aparezca "Nequi" casi siempre es la firma de Nequi, no un pedido de plata
_BILLETERAS = re.compile(r"(?i)\b(nequi|daviplata)\b")


def analizar(texto: str) -> dict:
    from .senales import normalizar

    # Las señales del texto se buscan sin los enlaces: "/clave" en una dirección no es pedir la clave
    sin_enlaces = enlaces._ENLACE.sub(" enlace ", texto)
    senales = detectar(_BILLETERAS.sub("billetera", sin_enlaces))
    limpio = normalizar(texto)
    if _ENTREGA_CODIGO.search(limpio) and not _REENVIAR.search(limpio):
        senales = [s for s in senales if s.id != "pide_codigo"]
    revisados = [enlaces.revisar(e) for e in enlaces.extraer(texto)]
    no_oficiales = [e for e in revisados if not e.oficial]
    # Lo del enlace va primero: es la razón principal del aviso cuando aparece
    de_enlace = []
    if any(e.suplanta for e in revisados):
        de_enlace.append(ENLACE_SUPLANTA)
    if any(e.sospechoso and not e.suplanta for e in revisados):
        de_enlace.append(ENLACE_SOSPECHOSO)
    if no_oficiales and PIDE_ENTRAR.patron.search(normalizar(sin_enlaces)):
        de_enlace.append(PIDE_ENTRAR)
    senales = de_enlace + [replace(s, motivo=_MOTIVOS.get(s.id, s.motivo)) for s in senales]
    nivel = calcular_nivel(senales)
    return {
        "nivel": nivel.etiqueta,
        "mensaje": mensaje(nivel, senales, ACCIONES),
        "senales": [{"id": s.id, "tipo": s.tipo, "motivo": s.motivo} for s in senales],
        "enlaces": [
            {"enlace": e.texto, "dominio": e.dominio, "oficial": e.oficial, "imita": e.imita, "hallazgos": e.hallazgos}
            for e in revisados
        ],
        "limite": "Centinela no abre los enlaces: no sabe si la página es nueva ni qué contiene. "
                  "Un enlace sin hallazgos no es garantía de que sea seguro.",
    }


@router.post("/mensajes/analizar", dependencies=[Depends(limite_mensajes)])
def analizar_mensaje(entrada: MensajeEntrada):
    return analizar(entrada.texto)
