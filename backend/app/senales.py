"""Catálogo de señales de riesgo y cálculo del nivel de riesgo.

Las señales son reglas de referencia sobre el contenido de la conversación,
no sobre la voz, el acento ni las características de quien habla. Cada nivel
se decide con reglas verificables y no se muestran porcentajes de certeza,
porque todavía no hay una validación estadística que los respalde.
"""
import re
import unicodedata
from dataclasses import dataclass
from enum import IntEnum


class Tipo:
    # Solicitud concreta de algo que permite robar dinero o la cuenta
    SOLICITUD = "solicitud"
    # Presión psicológica sobre la víctima
    PRESION = "presion"
    # Contexto que por sí solo no es fraude, pero pide precaución
    CONTEXTO = "contexto"


@dataclass(frozen=True)
class Senal:
    id: str
    tipo: str
    descripcion: str
    # Frase corta para el aviso, en segunda persona
    motivo: str
    patron: re.Pattern


def _p(regex: str) -> re.Pattern:
    return re.compile(regex)


CATALOGO: list[Senal] = [
    Senal(
        "pide_codigo",
        Tipo.SOLICITUD,
        "Pide un código de verificación, OTP, PIN, clave o contraseña.",
        "te piden un código o una clave",
        _p(r"\b(codigo|clave|contrasena|token|pin|otp)\b"),
    ),
    Senal(
        "pide_datos_bancarios",
        Tipo.SOLICITUD,
        "Pide número de tarjeta, CVV, fecha de vencimiento o número de cuenta.",
        "te piden datos de tu tarjeta o cuenta",
        _p(r"\b(numero de (la )?(tarjeta|cuenta)|cvv|cvc|fecha de vencimiento|los (tres|3) numeros de atras)\b"),
    ),
    Senal(
        "pide_transferencia",
        Tipo.SOLICITUD,
        "Pide transferir, consignar o girar dinero.",
        "te piden enviar dinero",
        _p(r"\b(transfier\w*|transferencia|consign\w*|gir(e|ar|en|ela|elo)|nequi|daviplata|cuenta segura)\b"),
    ),
    Senal(
        "acceso_remoto",
        Tipo.SOLICITUD,
        "Pide instalar una aplicación de acceso remoto o compartir la pantalla.",
        "te piden instalar una aplicación o compartir tu pantalla",
        _p(r"\b(anydesk|teamviewer|quicksupport|rustdesk|compart\w* (la |su |tu )?pantalla|instal\w* (una |la |esta )?(app|aplicacion))\b"),
    ),
    Senal(
        "desactivar_seguridad",
        Tipo.SOLICITUD,
        "Pide desactivar una protección, una alerta o la verificación en dos pasos.",
        "te piden desactivar una protección",
        _p(r"\b(desactiv\w*|apag\w*|quit\w*) (la |las |el |los )?(alerta|alertas|verificacion|seguridad|antivirus|notificaciones|biometria|huella)"),
    ),
    Senal(
        "urgencia",
        Tipo.PRESION,
        "Presiona para actuar de inmediato.",
        "te presionan para actuar rápido",
        _p(r"\b(urgente|ya mismo|de inmediato|inmediatamente|ahora mismo|rapido|en los proximos \d+ minutos|antes de que)\b"),
    ),
    Senal(
        "amenaza",
        Tipo.PRESION,
        "Amenaza con captura, embargo, bloqueo, demanda o daño.",
        "te amenazan",
        _p(r"\b(captur\w*|embarg\w*|bloque\w*|demand\w*|orden de arresto|le va a pasar|secuestr\w*|extorsion)\b"),
    ),
    Senal(
        "aislamiento",
        Tipo.PRESION,
        "Pide guardar secreto o no colgar.",
        "te piden no colgar o no contarle a nadie",
        _p(r"\b(no le (diga|cuente|comente)|no cuelgue|no cuelgues|no se lo diga|confidencial|no hable con nadie|entre usted y yo)\b"),
    ),
    Senal(
        "suplanta_entidad",
        Tipo.CONTEXTO,
        "Dice llamar de un banco, entidad pública, operador, mensajería o soporte técnico.",
        "dicen llamar de una entidad",
        _p(r"\b(banco|bancolombia|davivienda|fiscalia|policia|dian|gaula|soporte tecnico|servientrega|interrapidisimo|claro|movistar|tigo|superintendencia|bbva|colpatria|av villas|banco de bogota|caja social|nu ?bank|sijin|dijin|registraduria|cobro juridico|eps)\b"),
    ),
    Senal(
        "premio_inversion",
        Tipo.CONTEXTO,
        "Ofrece un premio, una inversión garantizada, un crédito o una devolución.",
        "te ofrecen un premio, crédito o ganancia",
        _p(r"\b(ganador|gano|premio|sorteo|inversion garantizada|rentabilidad|credito pre ?aprobado|devolucion de impuestos|reembolso)\b"),
    ),
    Senal(
        "finge_conocido",
        Tipo.CONTEXTO,
        "Dice ser un familiar o conocido con un número nuevo, o pide adivinar quién habla.",
        "dicen ser un conocido con número nuevo",
        _p(r"\bfinge ser conocido\b"),
    ),
    Senal(
        "pide_datos_personales",
        Tipo.CONTEXTO,
        "Pide número de cédula, fecha de nacimiento, dirección u otros datos personales.",
        "te piden datos personales",
        _p(r"\b(numero de cedula|su cedula|tu cedula|fecha de nacimiento|direccion de (su|tu) casa|donde vive|donde vives|nombre de (su|tu) madre)\b"),
    ),
]

# Frases con las que una entidad legítima advierte que NUNCA pide algo.
# Si aparecen justo antes de la señal, la solicitud no cuenta.
_NEGACION = re.compile(r"\b(nunca|jamas|no (le |te )?(vamos a |va a |vas a )?(pedi\w*|solicit\w*|preguntar\w*)|no comparta|no compartas|no de|no des|no entregue)\b")
_VENTANA_NEGACION = 45
# Quien cuenta que ya pagó o devolvió dinero no está pidiendo una transferencia
_INFORMATIVO = re.compile(r"\b(ya )?(le|te|les) (pase|consigne|transferi|mande|gire|devolvi|deposite)\b")


def normalizar(texto: str) -> str:
    """Minúsculas, sin tildes y con los modismos regionales llevados a su forma común."""
    from .modismos import llevar_a_forma_comun

    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return llevar_a_forma_comun(re.sub(r"\s+", " ", sin_tildes.lower()))


def detectar(texto: str) -> list[Senal]:
    """Devuelve las señales presentes en el texto, en el orden del catálogo."""
    limpio = normalizar(texto)
    encontradas = []
    for senal in CATALOGO:
        for m in senal.patron.finditer(limpio):
            previo = limpio[max(0, m.start() - _VENTANA_NEGACION): m.start()]
            if senal.id == "pide_transferencia" and _INFORMATIVO.search(previo + m.group(0)):
                continue
            if senal.tipo == Tipo.SOLICITUD and _NEGACION.search(previo):
                continue
            encontradas.append(senal)
            break
    return encontradas


# Señal que no sale del texto sino de los reportes de otras personas (paso 8).
# Es de contexto: sola llega como máximo a moderado y nunca decide sola (modelo de amenazas, A15).
NUMERO_REPORTADO = Senal(
    "numero_reportado",
    Tipo.CONTEXTO,
    "El número que llama tiene reportes de varias personas en Centinela (no confirmados)",
    "este número tiene reportes de otras personas",
    _p(r"(?!)"),
)


class Nivel(IntEnum):
    BAJO = 0
    MODERADO = 1
    ALTO = 2
    CRITICO = 3

    @property
    def etiqueta(self) -> str:
        return ["bajo", "moderado", "alto", "critico"][self]


def calcular_nivel(senales: list[Senal]) -> Nivel:
    """Reglas verificables:

    - crítico: una solicitud sensible junto con presión (urgencia, amenaza o aislamiento).
    - alto: una solicitud sensible, o tres o más señales de presión o contexto distintas.
    - moderado: al menos una señal de presión o contexto.
    - bajo: ninguna señal.
    """
    tipos = [s.tipo for s in senales]
    solicitud = Tipo.SOLICITUD in tipos
    presion = Tipo.PRESION in tipos
    if solicitud and presion:
        return Nivel.CRITICO
    if solicitud or len(senales) >= 3:
        return Nivel.ALTO
    if senales:
        return Nivel.MODERADO
    return Nivel.BAJO


_TITULOS = {
    Nivel.BAJO: "Sin señales de riesgo",
    Nivel.MODERADO: "PRECAUCIÓN",
    Nivel.ALTO: "RIESGO ALTO",
    Nivel.CRITICO: "RIESGO CRÍTICO",
}

_ACCIONES = {
    Nivel.BAJO: "No encontramos señales de estafa en lo que se ha dicho. Esto no garantiza que la llamada sea segura.",
    Nivel.MODERADO: "No compartas datos personales ni bancarios. Si dudas, cuelga y llama tú a la entidad por su número oficial.",
    Nivel.ALTO: "No lo hagas. Finaliza la llamada y verifica el contacto desde el canal oficial de la entidad.",
    Nivel.CRITICO: "Cuelga ahora. No compartas nada ni envíes dinero. Comunícate con tu banco por su canal oficial.",
}


def mensaje(nivel: Nivel, senales: list[Senal]) -> str:
    """Texto breve y accionable para la alerta."""
    if not senales:
        return f"{_TITULOS[nivel]}. {_ACCIONES[nivel]}"
    # La razón principal es la señal más grave: solicitud, luego presión, luego contexto
    orden = {Tipo.SOLICITUD: 0, Tipo.PRESION: 1, Tipo.CONTEXTO: 2}
    principal = min(senales, key=lambda s: orden[s.tipo])
    motivo = principal.motivo[0].upper() + principal.motivo[1:]
    return f"{_TITULOS[nivel]}. {motivo}. {_ACCIONES[nivel]}"
