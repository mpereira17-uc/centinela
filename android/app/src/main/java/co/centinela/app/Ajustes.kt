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

    // Para mostrar los ajustes una sola vez al abrir la app, sin insistir después
    var ajustesVistos: Boolean
        get() = prefs.getBoolean("ajustes_vistos", false)
        set(valor) = prefs.edit { putBoolean("ajustes_vistos", valor) }
}
