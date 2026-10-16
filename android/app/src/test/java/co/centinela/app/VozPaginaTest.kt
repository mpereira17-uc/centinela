package co.centinela.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class VozPaginaTest {
    @Test
    fun leeElAvisoQueLaPaginaPideDecir() {
        assertEquals(
            "Cuidado: te están pidiendo un código.",
            VozPagina.leer("""{"tipo":"decir","texto":"  Cuidado: te están pidiendo un código.\u0007 "}"""),
        )
    }

    @Test
    fun recortaLoLargoEIgnoraLoDemas() {
        assertEquals(VozPagina.MAXIMO, VozPagina.leer("""{"tipo":"decir","texto":"${"a".repeat(500)}"}""")!!.length)
        for (otro in listOf("""{"tipo":"decir","texto":""}""", """{"tipo":"pantalla","encendida":true}""", "no es json", null)) {
            assertNull(otro, VozPagina.leer(otro))
        }
    }
}
