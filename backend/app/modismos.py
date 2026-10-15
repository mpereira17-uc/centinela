"""Modismos y variantes regionales de Colombia.

Antes de buscar señales o calcular el clasificador, el texto (ya en minúsculas y sin
tildes) se lleva a una forma común: "los numeritos del mensajito" queda como "el codigo",
"cien lucas" como "cien mil pesos" y "pa'" como "para". Así una misma solicitud se
reconoce aunque se diga como en la Costa, en Antioquia, en el Valle o en Bogotá.

Solo se reemplazan expresiones, nunca se borran palabras, y no se tiene en cuenta
el acento de la voz: eso depende del transcriptor (ver docs/modismos.md).
"""
import re

# (patrón sobre texto normalizado, reemplazo). El orden importa: lo específico va primero.
_REGLAS: list[tuple[str, str]] = [
    # Contracciones y diminutivos frecuentes en la transcripción
    (r"\bpa'?(?= )", "para"),
    (r"\bpal\b", "para el"),
    (r"\bahorita\b", "ahora"),
    (r"\bmomentico\b", "momento"),
    (r"\brapidito\b", "rapido"),
    (r"\bligerito\b", "rapido"),

    # El código que llega por mensaje: "los numeritos", "el mensajito", "el codiguito"
    (r"\b(los|unos|esos) (numeritos|digitos|numeros) (que le (llego|llegaron|entro|entraron|aparecen?|salen?)|del (mensaje|mensajito|celular|texto))\b", "el codigo"),
    (r"\bnumeritos?\b", "codigo"),
    (r"\bcodiguito\b", "codigo"),
    (r"\bclavecita\b", "clave"),
    (r"\bmensajito\b", "mensaje"),
    (r"\bel token\b", "el codigo"),

    # Plata: "lucas", "barras", "palos", "melones"
    (r"\b(\w+) (lucas|lukas|barras|luquitas)\b", r"\1 mil pesos"),
    (r"\b(un|el) (palo|melon)\b", r"\1 millon"),
    (r"\b(\w+) (palos|melones)\b", r"\1 millones"),
    (r"\bplatica\b", "plata"),
    (r"\bbilletico\b", "plata"),

    # Pedir que mande dinero, dicho de forma coloquial
    (r"\b(mandeme|mandame|me manda|me mandas|paseme|pasame|me pasa|me pasas|eche|echeme|hagame el giro de|colabor(?:eme|enos|arnos|arme|e) con|regaleme|me regala|me presta|prestame) (unas |unos |la |una |esa )?(?:(\w+ )?(mil pesos|millones|millon|plata|pesos)|\w+ mil)\b",
     "transfiera la plata"),
    (r"\b(bre-?b|bre b|llave bre-?b)\b", "transferencia"),

    # Instalar o bajar una aplicación
    (r"\b(baje|bajese|descargue|descarguese|bajate|descargate|bajese) (de la tienda |del play store |de la play store )?(una |la |esta |esa )?(app|aplicacion|aplicacioncita)\b", "instale una aplicacion"),

    # Presión: modismos de afán
    (r"\b(hagale|dele|hagale pues|camine|corra) (ya|rapido|de una)\b", "urgente"),
    (r"\ba la de ya\b", "urgente"),
    (r"\b(es de afan|estoy de afan|con afan)\b", "urgente"),
    (r"\b(ahi mismo|ahi mismito|de una vez)\b", "ya mismo"),
    (r"\bvolando\b", "rapido"),

    # Amenazas con jerga
    (r"\b(le|te) caemos\b", "le va a pasar algo, amenaza"),
    (r"\b(lo|la|los) tenemos ubicad[oa]s?\b", "le va a pasar algo, amenaza"),
    (r"\bsabemos donde (vive|vives|trabaja|trabajas|estudia)\b", "le va a pasar algo, amenaza"),
    (r"\b(pagar|paga|pague|pagas|pagues) (la )?(vacuna|cuota de seguridad)\b", "extorsion amenaza"),
    (r"\bboleteo\b", "extorsion amenaza"),
    (r"\b(le|te|les) va a ir (muy )?mal\b", "le va a pasar algo, amenaza"),

    # Secreto y no colgar
    (r"\bno le vaya a (decir|contar|comentar)\b", "no le diga"),
    (r"\bno me vaya a colgar\b", "no cuelgue"),
    (r"\b(esto|eso) queda entre (los dos|nosotros)\b", "entre usted y yo"),
    (r"\bnada de llamar a la policia\b", "no le diga a la policia"),

    # Conocido que dice tener número nuevo
    (r"\badivin[ae] quien (le |te )?habla\b", "finge ser conocido"),
    (r"\b(este es|le hablo de|te hablo de) mi (numero|celular) nuevo\b", "finge ser conocido"),
    (r"\bse me (dano|perdio|robaron) el (celular|telefono)\b", "finge ser conocido"),
]

_COMPILADAS = [(re.compile(p), r) for p, r in _REGLAS]


def llevar_a_forma_comun(texto: str) -> str:
    """Reemplaza modismos regionales por su forma común. El texto ya viene normalizado."""
    for patron, reemplazo in _COMPILADAS:
        texto = patron.sub(reemplazo, texto)
    return texto
