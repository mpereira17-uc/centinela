"""Modo práctica: llamadas de mentira para aprender a reconocer estafas.

Toma llamadas de la base de guiones (las de prueba y las regionales, que no entrenan
el modelo) y explica en cada una qué la delataba. Sirve para personas mayores y para
probar la app con usuarios del piloto. No guarda nada: el puntaje queda en el navegador.
"""
import random
from datetime import date, datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query

from evaluacion import guiones

from .cuentas import LimitePorCliente
from .senales import Tipo, detectar

router = APIRouter(tags=["practica"])
# Generoso: en la sustentación varios jurados en el mismo wifi salen con la misma dirección
limite_practica = LimitePorCliente(maximo=90, ventana=60)
PARTICIONES = ("sintetica_prueba", "regional")
CONSEJO_LEGITIMA = "No pidió códigos, claves ni plata, y no te apuró. Aun así, si dudas, cuelga y llama tú por el canal oficial."
COLOMBIA = timezone(timedelta(hours=-5))  # sin horario de verano; no depende de tzdata (Windows no lo trae)

# Niveles por táctica, del más fácil de reconocer al más difícil. Cada uno mezcla sus estafas con
# llamadas normales parecidas (una tienda, un familiar, el banco de verdad), para que no baste
# con sospechar de todo lo que suene al tema.
NIVELES = (
    {"id": "premios", "nombre": "Premios y paquetes",
     "tactica": "Te ofrecen un premio o te retienen un paquete, y piden pagar primero.",
     "estafas": ("premio_falso", "envio_falso"), "normales": ("comercio", "domicilio")},
    {"id": "familiar", "nombre": "Familiar en apuros",
     "tactica": "Dicen ser de tu familia, con número nuevo o en una emergencia, y piden plata ya.",
     "estafas": ("familiar_falso",), "normales": ("familia",)},
    {"id": "urgencia", "nombre": "Urgencia con tu banco o tu operador",
     "tactica": "Te asustan con un fraude o una falla y piden un código o instalar una app.",
     "estafas": ("suplanta_banco", "soporte_falso"), "normales": ("banco", "banco_real", "servicios")},
    {"id": "autoridad", "nombre": "Autoridad y amenazas",
     "tactica": "Hablan como cobranza, juzgado o grupo armado, y te amenazan si no pagas.",
     "estafas": ("extorsion", "suplanta_entidad"), "normales": ("salud", "colegio", "trabajo")},
)
NIVEL_POR_ID = {n["id"]: n for n in NIVELES}
PATRON_NIVEL = "^(" + "|".join(NIVEL_POR_ID) + ")$"

# La estafa de la semana: modalidades que circulan en Colombia, explicadas en tres líneas
# (qué dicen, qué buscan, qué hacer) y ligadas al nivel donde se practican. Rota cada lunes.
SEMANALES = (
    {"titulo": "El falso asesor de seguridad del banco", "nivel": "urgencia", "lineas": (
        "Te llaman por una compra rara o un bloqueo en tu cuenta.",
        "Para «cancelarla» te piden el código que te llega por mensaje, o tu clave.",
        "El banco nunca te pide ese código. Cuelga y llama al número que está detrás de tu tarjeta.")},
    {"titulo": "El familiar con número nuevo", "nivel": "familiar", "lineas": (
        "Alguien dice ser tu hijo, tu sobrino o tu nieto y que cambió de número.",
        "Después cuenta una urgencia y pide que le mandes plata por Nequi o Daviplata.",
        "Llámalo al número de siempre o pregúntale la palabra clave de la familia.")},
    {"titulo": "El paquete retenido", "nivel": "premios", "lineas": (
        "Dicen ser de una transportadora y que tienes un paquete retenido en la bodega.",
        "Para entregarlo piden pagar un impuesto o el envío, por un enlace o una consignación.",
        "Si no esperas nada, no pagues. Revisa el envío en la página oficial de la transportadora.")},
    {"titulo": "La falsa cobranza o el embargo", "nivel": "autoridad", "lineas": (
        "Dicen ser de una oficina de cobro jurídico o de un juzgado y que te van a embargar.",
        "Te presionan para consignar hoy mismo a una cuenta que ellos te dan.",
        "Un embargo no se arregla con una llamada. Pide el documento por escrito y verifica con la entidad.")},
    {"titulo": "El falso técnico del operador", "nivel": "urgencia", "lineas": (
        "Te llaman por una falla en tu internet o en tu celular.",
        "Te piden instalar una app para «revisar» el equipo; con ella pueden ver tu pantalla y tus claves.",
        "No instales nada que te pidan por teléfono. Llama tú a la línea oficial de tu operador.")},
    {"titulo": "El premio que nunca jugaste", "nivel": "premios", "lineas": (
        "Te felicitan porque ganaste una moto, un mercado o un bono de un almacén.",
        "Para reclamarlo piden pagar el envío, un impuesto o una recarga.",
        "Un premio de verdad no se cobra para entregarlo. Si no participaste, no ganaste.")},
    {"titulo": "La emergencia de un familiar", "nivel": "familiar", "lineas": (
        "Alguien llama con afán: un familiar tuvo un accidente o está detenido.",
        "Piden plata ya para el hospital, la fianza o un abogado, y que no le cuentes a nadie.",
        "Cuelga y llama directamente a ese familiar o a alguien que esté con él.")},
    {"titulo": "La extorsión por teléfono", "nivel": "autoridad", "lineas": (
        "Dicen que te tienen ubicado y te amenazan a ti o a tu familia.",
        "Exigen una «cuota» o plata para dejarte tranquilo.",
        "Cuelga, no des datos y llama gratis al GAULA, línea 165.")},
)
_PRIMER_LUNES = date(2024, 1, 1)


def _pistas(g) -> list[str]:
    # Lo que delata la estafa: primero lo que piden, luego la presión y el contexto
    orden = {Tipo.SOLICITUD: 0, Tipo.PRESION: 1, Tipo.CONTEXTO: 2}
    vistas = {}
    for t in g.turnos:
        if t.hablante == "llamante":
            for s in detectar(t.texto):
                vistas.setdefault(s.id, s)
    return [s.motivo[0].upper() + s.motivo[1:] for s in sorted(vistas.values(), key=lambda s: orden[s.tipo])][:3]


def _ronda(g) -> dict:
    pistas = _pistas(g) if g.es_riesgo else []
    return {
        "id": g.id,
        "region": g.region,
        "etiqueta": g.etiqueta,
        "turnos": [{"hablante": t.hablante, "texto": t.texto} for t in g.turnos],
        "turno_riesgo": g.turno_riesgo,
        "pistas": pistas,
        # La frase donde está la trampa, para mostrarla resaltada al final
        "frase_clave": g.turnos[g.turno_riesgo].texto if g.es_riesgo else None,
        "explicacion": (g.descripcion + ".") if g.es_riesgo else CONSEJO_LEGITIMA,
    }


@router.get("/practica/niveles", dependencies=[Depends(limite_practica)])
def niveles():
    base = [g for g in guiones.cargar() if g.particion in PARTICIONES]
    return [
        {"id": n["id"], "numero": i, "nombre": n["nombre"], "tactica": n["tactica"],
         "llamadas": sum(g.categoria in n["estafas"] + n["normales"] for g in base)}
        for i, n in enumerate(NIVELES, start=1)
    ]


def estafa_de_la_semana(hoy: date | None = None) -> dict:
    hoy = hoy or datetime.now(COLOMBIA).date()
    semana = (hoy - _PRIMER_LUNES).days // 7
    s = SEMANALES[semana % len(SEMANALES)]
    lunes = _PRIMER_LUNES + timedelta(weeks=semana)
    nivel = NIVEL_POR_ID[s["nivel"]]
    return {"semana": lunes.isoformat(), "titulo": s["titulo"], "lineas": list(s["lineas"]),
            "nivel": nivel["id"], "nivel_nombre": nivel["nombre"]}


@router.get("/practica/semana", dependencies=[Depends(limite_practica)])
def semana():
    return estafa_de_la_semana()


@router.get("/practica/rondas", dependencies=[Depends(limite_practica)])
def rondas(cantidad: int = Query(5, ge=1, le=10), semilla: int | None = Query(None, ge=0),
           nivel: str | None = Query(None, pattern=PATRON_NIVEL)):
    base = [g for g in guiones.cargar() if g.particion in PARTICIONES]
    if nivel:
        n = NIVEL_POR_ID[nivel]
        base = [g for g in base if g.categoria in n["estafas"] + n["normales"]]
    azar = random.Random(semilla)
    riesgo = [g for g in base if g.es_riesgo]
    legit = [g for g in base if not g.es_riesgo]
    # Mitad y mitad (con una de más al azar), para que adivinar siempre "estafa" no gane
    n_riesgo = cantidad // 2 + (azar.random() < 0.5 if cantidad % 2 else 0)
    elegidas = azar.sample(riesgo, n_riesgo) + azar.sample(legit, cantidad - n_riesgo)
    azar.shuffle(elegidas)
    return [_ronda(g) for g in elegidas]
