package co.centinela.app

import org.json.JSONException
import org.json.JSONObject

/**
 * "Compartir con Centinela": un mensaje que se comparte desde WhatsApp, Mensajes o el correo llega a
 * "Revisar un mensaje". El texto nunca va en la dirección de la página: la página lo pide por el canal
 * CentinelaApp y la app se lo entrega una sola vez.
 */
object Compartido {
    // El mismo límite del campo de la página y de /mensajes/analizar
    const val MAXIMO = 2000

    fun limpiar(texto: CharSequence?): String? = texto?.toString()?.trim()?.take(MAXIMO)?.ifEmpty { null }

    fun esPedido(mensaje: String?): Boolean {
        if (mensaje == null) return false
        return try {
            JSONObject(mensaje).optString("tipo") == "pedir-compartido"
        } catch (e: JSONException) {
            false
        }
    }

    fun respuesta(texto: String?): String = JSONObject().put("tipo", "compartido").put("texto", texto.orEmpty()).toString()
}
