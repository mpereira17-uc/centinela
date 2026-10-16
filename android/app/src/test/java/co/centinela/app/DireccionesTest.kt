package co.centinela.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class DireccionesTest {
    @Test
    fun aceptaLaDireccionBaseConHttps() {
        assertEquals("https://demo.trycloudflare.com", Direcciones.normalizar("  https://demo.trycloudflare.com/ "))
        assertEquals("https://centinela.example.co:8443", Direcciones.normalizar("https://centinela.example.co:8443"))
    }

    @Test
    fun rechazaLoQueNoEsSeguroOEsRaro() {
        for (mala in listOf(
            "http://demo.trycloudflare.com",
            "demo.trycloudflare.com",
            "https://",
            "https://demo.trycloudflare.com/otra/ruta",
            "https://demo.trycloudflare.com/?x=1",
            "https://usuario@demo.trycloudflare.com",
            "javascript:alert(1)",
            "",
        )) {
            assertNull(mala, Direcciones.normalizar(mala))
        }
    }
}
