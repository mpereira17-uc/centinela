package co.centinela.app

import org.json.JSONArray
import org.json.JSONException
import org.json.JSONObject

/** Una llamada que Centinela rechazó, para que la persona la revise después. */
data class LlamadaRechazada(val numero: String, val fecha: Long, val titulo: String)

/**
 * Bloqueo opcional de estafas confirmadas. Viene apagado: un reporte puede estar equivocado y la
 * persona debe decidir si prefiere no recibir esas llamadas. Encendido, solo rechaza números en
 * "estafa_confirmada" (varias personas dicen que perdieron dinero o datos), nunca por un solo reporte,
 * publicidad o reportes que se contradicen. Cada rechazo queda anotado y se puede permitir el número.
 */
object Bloqueo {
    const val MAXIMO_REGISTRO = 50

    fun rechazar(rep: Reputacion?, activado: Boolean, numero: String, permitidos: Set<String>): Boolean =
        activado && rep?.estado == "estafa_confirmada" && clave(numero) !in permitidos

    /** El mismo número con o sin +57, espacios o guiones queda igual. */
    fun clave(numero: String): String {
        val d = numero.filter(Char::isDigit)
        return if (d.length == 12 && d.startsWith("57")) d.drop(2) else d
    }

    fun anotar(registro: List<LlamadaRechazada>, nueva: LlamadaRechazada): List<LlamadaRechazada> =
        (listOf(nueva) + registro).take(MAXIMO_REGISTRO)

    fun aJson(registro: List<LlamadaRechazada>): String = JSONArray().apply {
        registro.forEach { put(JSONObject().put("numero", it.numero).put("fecha", it.fecha).put("titulo", it.titulo)) }
    }.toString()

    /** Lo que no se entienda se descarta, para que un dato dañado no deje sin ajustes a la app. */
    fun desdeJson(texto: String?): List<LlamadaRechazada> {
        val lista = try {
            JSONArray(texto ?: return emptyList())
        } catch (e: JSONException) {
            return emptyList()
        }
        return (0 until lista.length()).mapNotNull { i ->
            val j = lista.optJSONObject(i) ?: return@mapNotNull null
            val numero = j.optString("numero")
            if (numero.isBlank()) null else LlamadaRechazada(numero, j.optLong("fecha"), j.optString("titulo"))
        }.take(MAXIMO_REGISTRO)
    }
}
