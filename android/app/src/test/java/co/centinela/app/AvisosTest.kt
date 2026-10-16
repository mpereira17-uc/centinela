package co.centinela.app

import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Assert.assertTrue
import org.junit.Test

class AvisosTest {
    private fun rep(estado: String) = Reputacion(estado, "Mensaje del servidor", 3)

    @Test
    fun sinReportesNoMolesta() {
        assertNull(Avisos.para(rep("sin_reportes"), silenciarRiesgoAlto = true))
    }

    @Test
    fun usaElMensajeDelServidor() {
        val aviso = Avisos.para(rep("varios_reportes"), silenciarRiesgoAlto = false)!!
        assertEquals("Posible estafa", aviso.titulo)
        assertEquals("Mensaje del servidor", aviso.texto)
    }

    @Test
    fun soloSilenciaRiesgoAltoYSiLaPersonaLoPidio() {
        assertTrue(Avisos.para(rep("estafa_confirmada"), silenciarRiesgoAlto = true)!!.silenciar)
        assertTrue(Avisos.para(rep("varios_reportes"), silenciarRiesgoAlto = true)!!.silenciar)
        assertFalse(Avisos.para(rep("estafa_confirmada"), silenciarRiesgoAlto = false)!!.silenciar)
        // Un solo reporte, publicidad o reportes en disputa nunca silencian
        for (estado in listOf("reportado", "publicidad", "en_disputa", "en_revision")) {
            assertFalse(estado, Avisos.para(rep(estado), silenciarRiesgoAlto = true)!!.silenciar)
        }
    }

    @Test
    fun distingueCallCenterDeEstafa() {
        assertEquals("Publicidad o call center", Avisos.para(rep("publicidad"), false)!!.titulo)
    }

    @Test
    fun estadoNuevoDelServidorNoRompeLaApp() {
        assertEquals("Número con reportes", Avisos.para(rep("otro_estado"), false)!!.titulo)
    }

    @Test
    fun leeLaRespuestaDelServidor() {
        val r = Reputacion.desdeJson("""{"reportes": 4, "estado": "varios_reportes", "mensaje": "4 personas…", "senal": true}""")
        assertEquals(Reputacion("varios_reportes", "4 personas…", 4), r)
    }
}
