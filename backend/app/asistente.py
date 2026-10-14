"""Asistente por voz con un conjunto cerrado de comandos.

La voz solo sirve para consultar. Nunca ejecuta acciones sensibles como
desactivar la protección, borrar datos o compartir información: para eso se
pide una confirmación en pantalla (modelo de amenazas, A18). Las respuestas
solo prometen lo que Centinela hace de verdad (A20).
"""
import re
from dataclasses import dataclass

from .modelos import Llamada
from .senales import normalizar


@dataclass(frozen=True)
class Comando:
    id: str
    ejemplo: str
    patron: re.Pattern


def _p(regex: str) -> re.Pattern:
    return re.compile(regex)


# El orden importa: las acciones sensibles se revisan primero para que nunca
# se confundan con una consulta.
COMANDOS: list[Comando] = [
    Comando(
        "accion_sensible",
        "Desactiva la protección",
        _p(r"\b(desactiv\w*|apag\w*|quit\w*|borr\w*|elimin\w*|cambi\w* (mi |la )?(clave|contrasena|pin)|comparte|envia|transfier\w*|pag\w*)\b"),
    ),
    Comando("explicar_alerta", "Explícame la alerta", _p(r"\b(explic\w*|por que|que significa|que quiere decir)\b")),
    Comando("parece_estafa", "¿Esta llamada parece una estafa?", _p(r"\b(estafa|fraude|enga\w*|es seguro|es segura|riesgo)\b")),
    Comando("analizar_llamada", "Analiza esta llamada", _p(r"\b(analiz\w*|revis\w*|escuch\w*)\b")),
    Comando("verificar_identidad", "Ayúdame a verificar la identidad de esta persona", _p(r"\b(verific\w*|identidad|quien es|es real|es de verdad)\b")),
    Comando("reportar_numero", "Quiero reportar este número", _p(r"\b(report\w*|denunci\w*)\b")),
    Comando("activar_proteccion", "Activa mi protección", _p(r"\b(activ\w*|protec\w*|protege\w*)\b")),
    Comando("ayuda", "¿Qué puedes hacer?", _p(r"\b(ayuda|que puedes|que haces|comandos|opciones)\b")),
]

NIVELES_HABLADOS = {"bajo": "bajo", "moderado": "moderado", "alto": "alto", "critico": "crítico"}


@dataclass
class Respuesta:
    intencion: str
    texto: str
    # Si la acción pedida exige una confirmación fuera de la voz
    requiere_confirmacion: bool = False


def interpretar(texto: str) -> str:
    limpio = normalizar(texto)
    for comando in COMANDOS:
        if comando.patron.search(limpio):
            return comando.id
    return "desconocido"


def _ultima_decision(llamada: Llamada | None, estrategia: str):
    if not llamada or not llamada.fragmentos:
        return None
    return next(d for d in llamada.fragmentos[-1].decisiones if d.estrategia == estrategia)


def responder(texto: str, llamada: Llamada | None, estrategia: str) -> Respuesta:
    intencion = interpretar(texto)
    decision = _ultima_decision(llamada, estrategia)

    if intencion == "accion_sensible":
        return Respuesta(
            intencion,
            "Eso no lo hago por voz. Las acciones que cambian tu cuenta o tu protección "
            "se confirman en la pantalla, con tu PIN o tu huella. Nunca compartas claves ni envíes dinero por una llamada.",
            requiere_confirmacion=True,
        )

    if intencion in ("parece_estafa", "explicar_alerta"):
        if not decision:
            return Respuesta(
                intencion,
                "Todavía no hay nada que analizar. Escribe o graba lo que te están diciendo y te digo qué tan riesgoso parece.",
            )
        nivel = NIVELES_HABLADOS[decision.nivel]
        if intencion == "parece_estafa":
            return Respuesta(intencion, f"El riesgo es {nivel}. {decision.mensaje.split('. ', 1)[1]}")
        if not decision.senales:
            return Respuesta(intencion, f"El riesgo es {nivel} porque no encontré señales de estafa. Esto no garantiza que la llamada sea segura.")
        razones = "; ".join(s.descripcion[0].lower() + s.descripcion[1:].rstrip(".") for s in decision.senales)
        return Respuesta(intencion, f"El riesgo es {nivel} porque encontré esto: {razones}. Recuerda que puedo equivocarme.")

    if intencion == "analizar_llamada":
        return Respuesta(
            intencion,
            "No puedo escuchar las llamadas de tu celular. Escribe lo que te dicen o graba la conversación "
            "con el permiso de todos, y la analizo aquí mismo.",
        )

    if intencion == "verificar_identidad":
        return Respuesta(
            intencion,
            "No confíes solo en la voz: hoy se puede imitar con inteligencia artificial. Cuelga y llama tú "
            "al número oficial de la entidad o de la persona. Si es un familiar, hazle una pregunta que solo él o ella sepa responder.",
        )

    if intencion == "reportar_numero":
        return Respuesta(intencion, "Reportar números todavía no está disponible en esta versión de prueba.")

    if intencion == "activar_proteccion":
        return Respuesta(
            intencion,
            "Centinela no puede vigilar tus llamadas en segundo plano. Funciona cuando le das el texto o el audio de una conversación.",
        )

    if intencion == "ayuda":
        return Respuesta(
            intencion,
            "Puedes preguntarme si esta llamada parece una estafa, pedirme que te explique la alerta, "
            "o pedirme ayuda para verificar la identidad de quien te llama.",
        )

    return Respuesta(
        intencion,
        "No entendí. Puedes decir: ¿esta llamada parece una estafa?, explícame la alerta, o ayúdame a verificar la identidad.",
    )
