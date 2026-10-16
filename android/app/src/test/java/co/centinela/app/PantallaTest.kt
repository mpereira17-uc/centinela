package co.centinela.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class PantallaTest {
    @Test
    fun leeElPedidoDeLaPagina() {
        assertEquals(true, Pantalla.leer("""{"tipo":"pantalla","encendida":true}"""))
        assertEquals(false, Pantalla.leer("""{"tipo":"pantalla","encendida":false}"""))
    }

    @Test
    fun ignoraLoQueNoEsDeLaPantalla() {
        for (otro in listOf("""{"tipo":"contacto-quitado"}""", """{"tipo":"pantalla"}""", "no es json", null)) {
            assertNull(otro, Pantalla.leer(otro))
        }
    }
}
