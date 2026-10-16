package co.centinela.app

import org.json.JSONException
import org.json.JSONObject

/**
 * El modo acompañante escucha por el micrófono una llamada en altavoz. Si la pantalla se apaga, Android
 * pausa la página y el micrófono deja de oír, así que mientras escucha la página le pide a la app que no
 * la apague. El navegador lo hace con wakeLock, que dentro de la app no está disponible.
 */
object Pantalla {
    /** true para mantenerla encendida, false para soltarla, null si el mensaje no es de la pantalla. */
    fun leer(texto: String?): Boolean? {
        val j = try {
            JSONObject(texto ?: return null)
        } catch (e: JSONException) {
            return null
        }
        if (j.optString("tipo") != "pantalla" || !j.has("encendida")) return null
        return j.optBoolean("encendida", false)
    }
}
