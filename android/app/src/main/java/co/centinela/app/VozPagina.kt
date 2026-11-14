package co.centinela.app

import android.content.Context
import android.speech.tts.TextToSpeech
import org.json.JSONException
import org.json.JSONObject
import java.util.Locale

/**
 * Aviso hablado durante la llamada por Centinela y el modo acompañante. La página pide decir el aviso
 * ("Cuidado: te están pidiendo un código…") y la app lo dice con la voz del sistema, porque el WebView no
 * trae voz propia. Solo dice frases cortas y sin caracteres de control; sin voz en español no dice nada.
 */
class VozPagina(context: Context) {
    companion object {
        const val MAXIMO = 200

        /** El texto a decir, o null si el mensaje no es de este tipo o no se puede decir. */
        fun leer(texto: String?): String? {
            val j = try {
                JSONObject(texto ?: return null)
            } catch (e: JSONException) {
                return null
            }
            if (j.optString("tipo") != "decir") return null
            return j.optString("texto").filterNot(Char::isISOControl).trim().take(MAXIMO).ifEmpty { null }
        }
    }

    private var lista = false
    private var pendiente: String? = null
    private val voz: TextToSpeech = TextToSpeech(context.applicationContext) { estado ->
        lista = estado == TextToSpeech.SUCCESS && elegirIdioma()
        if (lista) pendiente?.let(::decir)
        pendiente = null
    }

    private fun elegirIdioma(): Boolean {
        val idioma = listOf("es-CO", "es-US", "es-419", "es").map(Locale::forLanguageTag)
            .firstOrNull { voz.isLanguageAvailable(it) >= TextToSpeech.LANG_AVAILABLE } ?: return false
        voz.language = idioma
        return true
    }

    fun decir(texto: String) {
        if (!lista) {
            // La voz tarda un momento en cargar la primera vez; se dice apenas esté
            pendiente = texto
            return
        }
        voz.speak(texto, TextToSpeech.QUEUE_FLUSH, null, "aviso")
    }

    fun cerrar() {
        voz.stop()
        voz.shutdown()
    }
}
