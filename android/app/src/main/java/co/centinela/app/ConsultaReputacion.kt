package co.centinela.app

import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

object ConsultaReputacion {
    /**
     * Pregunta al servidor qué saben otros usuarios del número. Android da unos 5 segundos para decidir
     * qué hacer con la llamada, así que se espera menos; si no hay respuesta, la llamada entra normal.
     * Se usa POST para que el número no quede en los registros de acceso del servidor.
     */
    fun consultar(servidor: String, numero: String): Reputacion? {
        var con: HttpURLConnection? = null
        return try {
            con = URL("$servidor/numeros/consulta").openConnection() as HttpURLConnection
            con.requestMethod = "POST"
            con.connectTimeout = 2000
            con.readTimeout = 2000
            con.doOutput = true
            con.setRequestProperty("Content-Type", "application/json")
            con.outputStream.use { it.write(JSONObject().put("numero", numero).toString().toByteArray()) }
            if (con.responseCode != 200) null
            else Reputacion.desdeJson(con.inputStream.bufferedReader().use { it.readText() })
        } catch (e: Exception) {
            null
        } finally {
            con?.disconnect()
        }
    }
}
