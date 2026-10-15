import pytest

from app.senales import CATALOGO, Nivel, calcular_nivel, detectar, mensaje


def ids(texto):
    return [s.id for s in detectar(texto)]


@pytest.mark.parametrize(
    "texto, esperada",
    [
        ("Dígame el código que le llegó por mensaje", "pide_codigo"),
        ("Necesito los tres números de atrás de la tarjeta", "pide_datos_bancarios"),
        ("Hágame una transferencia a esta cuenta segura", "pide_transferencia"),
        ("Instale AnyDesk para ayudarle", "acceso_remoto"),
        ("Desactive la verificación en dos pasos", "desactivar_seguridad"),
        ("Es urgente, tiene que ser ya mismo", "urgencia"),
        ("Si no paga hay orden de arresto", "amenaza"),
        ("No cuelgue y no le diga a nadie", "aislamiento"),
        ("Le hablamos del Banco de Bogotá", "suplanta_entidad"),
        ("Usted es el ganador de un sorteo", "premio_inversion"),
        ("Confírmeme su fecha de nacimiento", "pide_datos_personales"),
        ("Quiubo, ¿adivine quién le habla?", "finge_conocido"),
        ("Su hijo tuvo un accidente y está en la clínica", "emergencia_familiar"),
    ],
)
def test_cada_senal_del_catalogo_se_detecta(texto, esperada):
    assert esperada in ids(texto)


def test_todas_las_senales_tienen_un_caso_de_prueba():
    probadas = {
        "pide_codigo", "pide_datos_bancarios", "pide_transferencia", "acceso_remoto",
        "desactivar_seguridad", "urgencia", "amenaza", "aislamiento",
        "suplanta_entidad", "premio_inversion", "pide_datos_personales", "finge_conocido", "emergencia_familiar",
    }
    assert probadas == {s.id for s in CATALOGO}


def test_tildes_y_mayusculas_no_afectan():
    assert ids("CONTRASEÑA") == ids("contrasena") == ["pide_codigo"]


def test_advertencia_legitima_no_cuenta_como_solicitud():
    # Los bancos suelen decir esto al final de una llamada legítima
    assert ids("Recuerde que nunca le pediremos su clave ni códigos") == []
    assert ids("No comparta su código con nadie") == []


def test_apellido_no_se_confunde_con_giro():
    assert "pide_transferencia" not in ids("Hablo con el señor Giraldo")


def test_conversacion_cotidiana_es_riesgo_bajo():
    senales = detectar("Hola mamá, ¿vienes a almorzar el domingo?")
    assert calcular_nivel(senales) == Nivel.BAJO


def test_niveles_siguen_las_reglas():
    contexto = detectar("Le llamamos del banco")
    assert calcular_nivel(contexto) == Nivel.MODERADO

    solicitud = detectar("Dígame el código")
    assert calcular_nivel(solicitud) == Nivel.ALTO

    tres_de_contexto = detectar("Del banco, es urgente, usted ganó un premio")
    assert calcular_nivel(tres_de_contexto) == Nivel.ALTO

    critico = detectar("Es urgente, dígame el código ya mismo")
    assert calcular_nivel(critico) == Nivel.CRITICO


def test_mensaje_nombra_la_razon_mas_grave_y_no_da_porcentajes():
    senales = detectar("Le hablamos del banco, dígame el código")
    texto = mensaje(calcular_nivel(senales), senales)
    assert texto.startswith("RIESGO ALTO. Te piden un código o una clave.")
    assert "%" not in texto


def test_mensaje_de_riesgo_bajo_no_promete_seguridad():
    texto = mensaje(Nivel.BAJO, [])
    assert "no garantiza" in texto



def test_emergencia_familiar_es_contexto_y_sola_no_alerta():
    from app.senales import Nivel, calcular_nivel, detectar
    for texto in ("Su hijo tuvo un accidente", "Mamá, estoy detenido en la estación", "Quedé varado en la vía"):
        ids = [s.id for s in detectar(texto)]
        assert "emergencia_familiar" in ids, texto
    assert calcular_nivel(detectar("Su hijo tuvo un accidente")) == Nivel.MODERADO
    assert calcular_nivel(detectar("Su hijo tuvo un accidente, consígneme ya mismo")) == Nivel.CRITICO
