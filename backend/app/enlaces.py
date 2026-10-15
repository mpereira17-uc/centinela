"""Revisión de enlaces dentro de un mensaje (SMS, WhatsApp, correo).

Todo se decide con el texto del enlace, sin abrirlo: Centinela nunca visita la
página (no hay costo, no se avisa al estafador y no hay riesgo de SSRF, modelo de
amenazas A24). Por eso no puede saber si una página es nueva o si ya la bloquearon;
solo mira cómo está escrito el enlace.
"""
import re
import unicodedata
from dataclasses import dataclass, field
from urllib.parse import urlsplit

# Dominios oficiales de marcas que los estafadores suelen imitar en Colombia.
# Un enlace a uno de ellos (o a un subdominio suyo) no se marca por la marca.
OFICIALES = {
    "bancolombia": ("bancolombia.com", "grupobancolombia.com", "bancolombia.com.co"),
    "davivienda": ("davivienda.com",),
    "nequi": ("nequi.com.co",),
    "daviplata": ("daviplata.com",),
    "bbva": ("bbva.com.co", "bbva.com"),
    "bancodebogota": ("bancodebogota.com", "bancodebogota.com.co"),
    "colpatria": ("scotiabankcolpatria.com",),
    "bancopopular": ("bancopopular.com.co",),
    "avvillas": ("avvillas.com.co",),
    "cajasocial": ("bancocajasocial.com",),
    "nubank": ("nu.com.co", "nubank.com.br"),
    "falabella": ("bancofalabella.com.co", "falabella.com.co"),
    "dian": ("dian.gov.co",),
    "policia": ("policia.gov.co",),
    "fiscalia": ("fiscalia.gov.co",),
    "simit": ("fcm.org.co", "simit.org.co"),
    "registraduria": ("registraduria.gov.co",),
    "servientrega": ("servientrega.com",),
    "interrapidisimo": ("interrapidisimo.com",),
    "coordinadora": ("coordinadora.com",),
    "claro": ("claro.com.co",),
    "movistar": ("movistar.co",),
    "tigo": ("tigo.com.co",),
    "whatsapp": ("whatsapp.com", "wa.me"),
    "mercadolibre": ("mercadolibre.com.co",),
}
NOMBRES = {
    "bancolombia": "Bancolombia", "davivienda": "Davivienda", "nequi": "Nequi", "daviplata": "Daviplata",
    "bbva": "BBVA", "bancodebogota": "el Banco de Bogotá", "colpatria": "Scotiabank Colpatria",
    "bancopopular": "el Banco Popular", "avvillas": "el Banco AV Villas", "cajasocial": "el Banco Caja Social",
    "nubank": "Nu", "falabella": "Falabella", "dian": "la DIAN", "policia": "la Policía", "fiscalia": "la Fiscalía",
    "simit": "el SIMIT", "registraduria": "la Registraduría", "servientrega": "Servientrega",
    "interrapidisimo": "Interrapidísimo", "coordinadora": "Coordinadora", "claro": "Claro", "movistar": "Movistar",
    "tigo": "Tigo", "whatsapp": "WhatsApp", "mercadolibre": "Mercado Libre",
}
ACORTADORES = {
    "bit.ly", "tinyurl.com", "cutt.ly", "is.gd", "t.co", "goo.su", "rebrand.ly", "shorturl.at",
    "acortar.link", "ow.ly", "rb.gy", "tiny.cc", "s.id", "v.gd", "t.ly", "short.io", "bitly.ws",
}
# Terminaciones baratas muy usadas en campañas de phishing. Solas no son prueba.
TLD_RIESGOSOS = {"xyz", "top", "click", "online", "site", "live", "shop", "info", "icu", "buzz", "cfd", "sbs", "rest", "lat", "vip", "work"}
_CONFUSABLES = str.maketrans({"0": "o", "1": "l", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})
_ENLACE = re.compile(r"(?i)\b((?:https?://|www\.)[^\s<>\"']+|(?:[a-z0-9-]+\.)+(?:com|co|net|org|xyz|top|click|online|site|live|shop|info|icu|buzz|cfd|sbs|rest|lat|vip|work|ly|me|gy|io|at|link|gd|cc|id|ws)(?:/[^\s<>\"']*)?)")
MAX_ENLACES = 5


@dataclass
class Enlace:
    texto: str
    dominio: str
    hallazgos: list[str] = field(default_factory=list)
    imita: str | None = None
    oficial: bool = False

    @property
    def suplanta(self) -> bool:
        return self.imita is not None and not self.oficial

    @property
    def sospechoso(self) -> bool:
        return bool(self.hallazgos)


def extraer(texto: str) -> list[str]:
    vistos = []
    for m in _ENLACE.finditer(texto):
        enlace = m.group(1).rstrip(".,;:!?)")
        if enlace not in vistos:
            vistos.append(enlace)
    return vistos[:MAX_ENLACES]


def _es_de(dominio: str, base: str) -> bool:
    return dominio == base or dominio.endswith("." + base)


def _plano(texto: str) -> str:
    sin_tildes = unicodedata.normalize("NFKD", texto).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z]", "", sin_tildes.lower().translate(_CONFUSABLES).replace("rn", "m").replace("vv", "w"))


def revisar(enlace: str) -> Enlace:
    url = enlace if re.match(r"(?i)https?://", enlace) else "http://" + enlace
    partes = urlsplit(url)
    dominio = (partes.hostname or "").lower().rstrip(".")
    r = Enlace(enlace, dominio)

    if re.fullmatch(r"[\d.]+|\[?[0-9a-f:]+\]?", dominio):
        r.hallazgos.append("usa una dirección numérica en lugar de un nombre")
    if dominio.startswith("xn--") or ".xn--" in dominio:
        r.hallazgos.append("usa letras de otros alfabetos que imitan las normales")
    if partes.username or "@" in partes.netloc:
        r.hallazgos.append("esconde el destino real detrás de una @")
    if any(_es_de(dominio, a) for a in ACORTADORES):
        r.hallazgos.append("es un enlace acortado que esconde a dónde lleva")
    if dominio.rsplit(".", 1)[-1] in TLD_RIESGOSOS:
        r.hallazgos.append(f"termina en .{dominio.rsplit('.', 1)[-1]}, una terminación muy usada en engaños")
    if dominio.count(".") >= 4:
        r.hallazgos.append("tiene demasiadas partes en el nombre")

    r.oficial = any(_es_de(dominio, d) for doms in OFICIALES.values() for d in doms) or dominio.endswith(".gov.co")
    if not r.oficial:
        plano = _plano(dominio)
        for marca in OFICIALES:
            if marca in plano:
                r.imita = marca
                r.hallazgos.insert(0, f"usa el nombre de {NOMBRES[marca]} pero no es su página oficial")
                break
    return r
