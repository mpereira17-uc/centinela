package co.centinela.app

import org.json.JSONObject
import java.net.URI

/** Lo que responde el servidor de Centinela sobre un número (POST /numeros/consulta). */
data class Reputacion(val estado: String, val mensaje: String, val reportes: Int) {
    companion object {
        fun desdeJson(texto: String): Reputacion {
            val j = JSONObject(texto)
            return Reputacion(j.getString("estado"), j.getString("mensaje"), j.optInt("reportes", 0))
        }
    }
}

/** El aviso que se muestra al entrar la llamada. */
/** [alto]: la comunidad lo marca como estafa con varios reportes; la tarjeta sobre la llamada se pinta en ámbar. */
data class Aviso(val titulo: String, val texto: String, val silenciar: Boolean, val alto: Boolean = false)

object Avisos {
    // Estados que cuentan como señal de estafa en el servidor (reportes.ESTADOS_CON_SENAL)
    private val RIESGO_ALTO = setOf("varios_reportes", "estafa_confirmada")

    /**
     * Decide qué decir de un número. Sin reportes no se avisa nada, para no volver ruido cada llamada.
     * Como mucho se silencia el timbre: el aviso nunca rechaza la llamada, porque un reporte puede estar
     * equivocado. Rechazar es aparte y solo si la persona encendió el bloqueo opcional (ver Bloqueo).
     */
    fun para(rep: Reputacion, silenciarRiesgoAlto: Boolean): Aviso? {
        if (rep.estado == "sin_reportes") return null
        val titulo = when (rep.estado) {
            "estafa_confirmada" -> "Probable estafa"
            "varios_reportes" -> "Posible estafa"
            "reportado" -> "Número reportado"
            "publicidad" -> "Publicidad o call center"
            "en_disputa" -> "Reportes que se contradicen"
            "en_revision" -> "Reportes en revisión"
            else -> "Número con reportes"
        }
        val alto = rep.estado in RIESGO_ALTO
        return Aviso(titulo, rep.mensaje, silenciar = silenciarRiesgoAlto && alto, alto = alto)
    }
}

object Direcciones {
    /**
     * Acepta solo la dirección base del servidor, con HTTPS: los números que llaman viajan a ese servidor,
     * así que nunca por un canal sin cifrar ni a una ruta escondida dentro de otra página.
     */
    fun normalizar(texto: String): String? {
        val limpio = texto.trim().trimEnd('/')
        val uri = try {
            URI(limpio)
        } catch (e: Exception) {
            return null
        }
        if (uri.scheme != "https" || uri.host.isNullOrBlank()) return null
        if (!uri.rawPath.isNullOrEmpty() || uri.rawQuery != null || uri.rawFragment != null || uri.rawUserInfo != null) return null
        return limpio
    }
}
