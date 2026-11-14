package co.centinela.app

import android.media.AudioManager
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class AvisoHabladoTest {
    private val alto = Aviso("Posible estafa", "Mensaje", silenciar = false, alto = true)
    private val normal = AudioManager.RINGER_MODE_NORMAL

    @Test
    fun diceElTituloYQueNoDeCodigos() {
        val frase = AvisoHablado.frase(alto)
        assertTrue(frase.startsWith("Cuidado: posible estafa."))
        assertTrue(frase.contains("no des códigos, claves ni plata"))
    }

    @Test
    fun noDiceElNumero() {
        assertFalse(AvisoHablado.frase(alto).any(Char::isDigit))
    }

    @Test
    fun hablaSoloConRiesgoAltoYTimbreNormal() {
        assertEquals(AvisoHablado.Modo.HABLAR_Y_VIBRAR, AvisoHablado.modo(alto, true, normal, noMolestar = false))
        assertEquals(AvisoHablado.Modo.VIBRAR, AvisoHablado.modo(alto, true, AudioManager.RINGER_MODE_VIBRATE, false))
        // Publicidad, un solo reporte o reportes en disputa no hablan
        assertEquals(AvisoHablado.Modo.NADA, AvisoHablado.modo(alto.copy(alto = false), true, normal, false))
    }

    @Test
    fun respetaElSilencioDeLaPersona() {
        assertEquals(AvisoHablado.Modo.NADA, AvisoHablado.modo(alto, true, AudioManager.RINGER_MODE_SILENT, false))
        assertEquals(AvisoHablado.Modo.NADA, AvisoHablado.modo(alto, true, normal, noMolestar = true))
        assertEquals(AvisoHablado.Modo.NADA, AvisoHablado.modo(alto.copy(silenciar = true), true, normal, false))
        assertEquals(AvisoHablado.Modo.NADA, AvisoHablado.modo(alto, activado = false, timbre = normal, noMolestar = false))
    }
}
