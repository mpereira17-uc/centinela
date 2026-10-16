package co.centinela.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class ContactosTest {
    @Test
    fun aceptaCelularesColombianos() {
        assertEquals("3001234567", Contactos.celular("300 123 4567"))
        assertEquals("3001234567", Contactos.celular("+57 300 123 4567"))
        for (malo in listOf("6011234567", "300123456", "30012345678", "", null)) {
            assertNull(malo, Contactos.celular(malo))
        }
    }

    @Test
    fun leeElContactoDeLaPagina() {
        val m = Contactos.leer("""{"tipo":"contacto","nombre":"  Laura ","telefono":"3001234567"}""")
        assertEquals(MensajeContacto.Guardar(Contacto("Laura", "3001234567")), m)
        assertEquals(MensajeContacto.Quitar, Contactos.leer("""{"tipo":"contacto-quitado"}"""))
    }

    @Test
    fun ignoraLoQueNoEntiende() {
        for (malo in listOf(
            """{"tipo":"contacto","nombre":"Laura","telefono":"6011234567"}""",
            """{"tipo":"llamar","telefono":"3001234567"}""",
            "no es json",
            null,
        )) {
            assertNull(malo, Contactos.leer(malo))
        }
    }

    @Test
    fun recortaElNombre() {
        val largo = "L".repeat(50)
        val m = Contactos.leer("""{"tipo":"contacto","nombre":"$largo","telefono":"3001234567"}""") as MensajeContacto.Guardar
        assertEquals(30, m.contacto.nombre.length)
    }

    @Test
    fun textoDelBoton() {
        assertEquals("Llamar a Laura", Contactos.textoLlamar(Contacto("Laura", "3001234567")))
        assertEquals("Llamar a mi contacto", Contactos.textoLlamar(Contacto("", "3001234567")))
    }
}
