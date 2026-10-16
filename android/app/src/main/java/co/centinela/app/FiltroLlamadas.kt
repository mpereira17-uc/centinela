package co.centinela.app

import android.telecom.Call
import android.telecom.CallScreeningService
import kotlin.concurrent.thread

/**
 * Filtro de llamadas de Android. El sistema lo llama solo para llamadas entrantes de números que no
 * están en los contactos, y solo si la persona eligió a Centinela como app de filtro.
 *
 * No recibe ni puede recibir el audio: únicamente el número. Con él consulta los reportes de la
 * comunidad y, si hay algo que decir, muestra un aviso mientras el teléfono timbra.
 */
class FiltroLlamadas : CallScreeningService() {
    override fun onScreenCall(details: Call.Details) {
        val ajustes = Ajustes(this)
        val numero = details.handle?.schemeSpecificPart
        if (details.callDirection != Call.Details.DIRECTION_INCOMING || numero.isNullOrBlank() || ajustes.servidor.isBlank()) {
            respondToCall(details, CallResponse.Builder().build())
            return
        }
        thread {
            val aviso = ConsultaReputacion.consultar(ajustes.servidor, numero)
                ?.let { Avisos.para(it, ajustes.silenciarRiesgoAlto) }
            // Nunca se rechaza ni se bloquea la llamada; a lo sumo se silencia el timbre si la persona lo pidió
            respondToCall(details, CallResponse.Builder().setSilenceCall(aviso?.silenciar == true).build())
            if (aviso != null) {
                // La notificación queda para después de colgar; la tarjeta se ve encima de la llamada
                Notificaciones.mostrar(this, numero, aviso)
                TarjetaLlamada.mostrar(this, numero, aviso)
            }
        }
    }
}
