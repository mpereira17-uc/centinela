"""Modismos y variantes regionales de Colombia: misma solicitud, distinta forma de decirla."""
import pytest

from app.senales import detectar, normalizar


def _ids(texto):
    return {s.id for s in detectar(texto)}


@pytest.mark.parametrize("texto,senal", [
    ("Léame los numeritos que le llegaron, ¿oíste?", "pide_codigo"),                 # costa caribe
    ("Regáleme el codiguito del mensajito, sumercé", "pide_codigo"),                 # bogotá
    ("Mándeme cien lucas al Nequi de un amigo", "pide_transferencia"),               # antioquia
    ("Mandame unas luquitas que estoy varado", "pide_transferencia"),                # valle
    ("Páguela por Bre-B ya mismo", "pide_transferencia"),
    ("Bájese una aplicación del Play Store", "acceso_remoto"),
    ("Hágale ya, que eso se vence", "urgencia"),
    ("Si no paga hoy le caemos al negocio", "amenaza"),
    ("Si no pagás la vacuna te va mal", "amenaza"),
    ("Lo tenemos ubicado, mijo", "amenaza"),
    ("No le vaya a contar a su mamá", "aislamiento"),
    ("No me vaya a colgar, sumercé", "aislamiento"),
    ("Tía, este es mi número nuevo", "finge_conocido"),
    ("Le hablamos de cobro jurídico", "suplanta_entidad"),
])
def test_un_modismo_se_reconoce_como_la_senal(texto, senal):
    assert senal in _ids(texto)


@pytest.mark.parametrize("texto", [
    "Ajá, mi llave, ¿qué más? ¿Vienes al partido?",
    "Quiubo, parce, ¿nos vemos a las siete?",
    "Sumercé, ¿me regala la dirección para el pedido?",
    "Ya le pasé por Nequi la plata que me prestó, revise",
    "Mijo, ya te consigné lo del mercado",
    "Le hablamos de su EPS para programar la vacuna de refuerzo",
    "Achichay, qué frío, mamita",
])
def test_hablar_con_modismos_no_es_una_solicitud(texto):
    assert not {"pide_codigo", "pide_transferencia", "acceso_remoto", "amenaza"} & _ids(texto)


def test_la_plata_coloquial_se_lleva_a_pesos():
    assert "cien mil pesos" in normalizar("son cien lucas")
    assert "dos millones" in normalizar("dos palos")
    assert normalizar("pa' la casa") == "para la casa"
