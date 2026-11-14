package co.centinela.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertTrue
import org.junit.Test

class BloqueoTest {
    private fun rep(estado: String) = Reputacion(estado, "Mensaje del servidor", 5)

    @Test
    fun apagadoNuncaRechaza() {
        assertFalse(Bloqueo.rechazar(rep("estafa_confirmada"), activado = false, numero = "3000000001", permitidos = emptySet()))
    }

    @Test
    fun soloRechazaEstafasConfirmadas() {
        assertTrue(Bloqueo.rechazar(rep("estafa_confirmada"), true, "3000000001", emptySet()))
        // Varios reportes sin pérdidas, un solo reporte, publicidad o reportes en disputa nunca se rechazan
        for (estado in listOf("varios_reportes", "reportado", "publicidad", "en_disputa", "en_revision", "sin_reportes")) {
            assertFalse(estado, Bloqueo.rechazar(rep(estado), true, "3000000001", emptySet()))
        }
    }

    @Test
    fun sinRespuestaDelServidorLaLlamadaEntra() {
        assertFalse(Bloqueo.rechazar(null, true, "3000000001", emptySet()))
    }

    @Test
    fun unNumeroPermitidoEntraConOSinIndicativo() {
        val permitidos = setOf(Bloqueo.clave("300 000 0001"))
        assertFalse(Bloqueo.rechazar(rep("estafa_confirmada"), true, "+573000000001", permitidos))
        assertFalse(Bloqueo.rechazar(rep("estafa_confirmada"), true, "3000000001", permitidos))
        assertTrue(Bloqueo.rechazar(rep("estafa_confirmada"), true, "3000000002", permitidos))
    }

    @Test
    fun elRegistroGuardaLoMasRecientePrimeroYTieneTope() {
        var registro = emptyList<LlamadaRechazada>()
        for (i in 1..60) registro = Bloqueo.anotar(registro, LlamadaRechazada("30000000%02d".format(i), i.toLong(), "Probable estafa"))
        assertEquals(Bloqueo.MAXIMO_REGISTRO, registro.size)
        assertEquals("3000000060", registro.first().numero)
    }

    @Test
    fun elRegistroSobreviveAGuardarseYUnDatoDanadoNoRompe() {
        val registro = listOf(LlamadaRechazada("+573000000001", 1_760_000_000_000, "Probable estafa"))
        assertEquals(registro, Bloqueo.desdeJson(Bloqueo.aJson(registro)))
        assertEquals(emptyList<LlamadaRechazada>(), Bloqueo.desdeJson("{dañado"))
        assertEquals(emptyList<LlamadaRechazada>(), Bloqueo.desdeJson(null))
        assertEquals(1, Bloqueo.desdeJson("""[{"numero": "3000000001", "fecha": 5}, {"fecha": 6}, 7]""").size)
    }
}
