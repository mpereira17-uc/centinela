package co.centinela.app

import android.content.Context
import androidx.core.content.edit

/** Preferencias guardadas solo en este celular. */
class Ajustes(context: Context) {
    private val prefs = context.getSharedPreferences("centinela", Context.MODE_PRIVATE)

    var servidor: String
        get() = prefs.getString("servidor", "") ?: ""
        set(valor) = prefs.edit { putString("servidor", valor) }

    var silenciarRiesgoAlto: Boolean
        get() = prefs.getBoolean("silenciar_riesgo_alto", false)
        set(valor) = prefs.edit { putBoolean("silenciar_riesgo_alto", valor) }

    var avisoHablado: Boolean
        get() = prefs.getBoolean("aviso_hablado", true)
        set(valor) = prefs.edit { putBoolean("aviso_hablado", valor) }

    // Lo guarda la interfaz web (Ayuda > Contacto de confianza) para ofrecer "Llamar a …" en el aviso
    var contacto: Contacto?
        get() {
            val telefono = Contactos.celular(prefs.getString("contacto_telefono", null)) ?: return null
            return Contacto(prefs.getString("contacto_nombre", "") ?: "", telefono)
        }
        set(valor) = prefs.edit {
            if (valor == null) {
                remove("contacto_nombre")
                remove("contacto_telefono")
            } else {
                putString("contacto_nombre", valor.nombre)
                putString("contacto_telefono", valor.telefono)
            }
        }

    fun recibir(mensaje: MensajeContacto) {
        contacto = when (mensaje) {
            is MensajeContacto.Guardar -> mensaje.contacto
            MensajeContacto.Quitar -> null
        }
    }

    // Para mostrar los ajustes una sola vez al abrir la app, sin insistir después
    var ajustesVistos: Boolean
        get() = prefs.getBoolean("ajustes_vistos", false)
        set(valor) = prefs.edit { putBoolean("ajustes_vistos", valor) }
}
