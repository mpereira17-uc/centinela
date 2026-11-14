package co.centinela.app

import org.json.JSONObject
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class CompartidoTest {
    @Test
    fun recortaComoLaPagina() {
        assertEquals("Su paquete está retenido", Compartido.limpiar("  Su paquete está retenido \n"))
        assertEquals(Compartido.MAXIMO, Compartido.limpiar("a".repeat(5000))!!.length)
        assertNull(Compartido.limpiar("   "))
        assertNull(Compartido.limpiar(null))
    }

    @Test
    fun soloEntregaCuandoLaPaginaLoPide() {
        assertTrue(Compartido.esPedido("""{"tipo":"pedir-compartido"}"""))
        assertFalse(Compartido.esPedido("""{"tipo":"contacto","telefono":"3001234567"}"""))
        assertFalse(Compartido.esPedido("no es json"))
        assertFalse(Compartido.esPedido(null))
    }

    @Test
    fun laRespuestaLlevaElTextoSinRomperElJson() {
        val texto = "Ingrese a \"bit.ly/x\"\ny confirme"
        val j = JSONObject(Compartido.respuesta(texto))
        assertEquals("compartido", j.getString("tipo"))
        assertEquals(texto, j.getString("texto"))
        assertEquals("", JSONObject(Compartido.respuesta(null)).getString("texto"))
    }
}
