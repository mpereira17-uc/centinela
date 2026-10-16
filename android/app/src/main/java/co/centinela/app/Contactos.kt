package co.centinela.app

import org.json.JSONException
import org.json.JSONObject

/** El contacto de confianza que la persona guardó en Ayuda. Queda solo en este celular. */
data class Contacto(val nombre: String, val telefono: String)

/** Lo que la interfaz web le cuenta a la app sobre el contacto de confianza. */
sealed interface MensajeContacto {
    data class Guardar(val contacto: Contacto) : MensajeContacto
    data object Quitar : MensajeContacto
}

object Contactos {
    /** Celular colombiano de 10 dígitos que empieza por 3, con o sin +57, como lo valida la interfaz web. */
    fun celular(texto: String?): String? {
        var d = texto.orEmpty().filter(Char::isDigit)
        if (d.length == 12 && d.startsWith("57")) d = d.drop(2)
        return if (Regex("3\\d{9}").matches(d)) d else null
    }

    /**
     * Lee el mensaje de la página. Lo que no se entienda se ignora: la app nunca guarda un número que
     * no sea un celular válido, ni un nombre largo o con caracteres de control.
     */
    fun leer(texto: String?): MensajeContacto? {
        val j = try {
            JSONObject(texto ?: return null)
        } catch (e: JSONException) {
            return null
        }
        return when (j.optString("tipo")) {
            "contacto" -> celular(j.optString("telefono"))?.let { telefono ->
                val nombre = j.optString("nombre").filterNot(Char::isISOControl).trim().take(30)
                MensajeContacto.Guardar(Contacto(nombre, telefono))
            }
            "contacto-quitado" -> MensajeContacto.Quitar
            else -> null
        }
    }

    /** El texto del botón en el aviso: "Llamar a Laura", o "Llamar a mi contacto" si no tiene nombre. */
    fun textoLlamar(contacto: Contacto) = "Llamar a ${contacto.nombre.ifBlank { "mi contacto" }}"
}
