package co.centinela.app

import android.content.Context
import android.content.Intent
import android.graphics.PixelFormat
import android.media.AudioManager
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.provider.Settings
import android.view.ContextThemeWrapper
import android.view.Gravity
import android.view.LayoutInflater
import android.view.View
import android.view.WindowManager
import android.widget.TextView

/**
 * Tarjeta encima de la pantalla de llamada entrante, como la de un identificador de llamadas.
 *
 * Solo aparece si la persona dio el permiso "Mostrar sobre otras apps"; si no, queda la notificación.
 * Se quita sola cuando termina la llamada. Para saberlo se mira el modo de audio del celular, que no
 * pide permiso de llamadas ni de estado del teléfono.
 */
object TarjetaLlamada {
    private val principal = Handler(Looper.getMainLooper())
    private var vista: View? = null
    private const val REVISAR_CADA = 1000L
    // Por si el modo de audio no cambia en algún celular: nunca se queda pegada
    private const val MAXIMO = 90_000L

    fun puedeMostrarse(context: Context) = Settings.canDrawOverlays(context)

    fun mostrar(context: Context, numero: String, aviso: Aviso) {
        val app = context.applicationContext
        if (!puedeMostrarse(app)) return
        principal.post { pintar(app, numero, aviso) }
    }

    private fun pintar(app: Context, numero: String, aviso: Aviso) {
        quitar(app)
        val ventanas = app.getSystemService(WindowManager::class.java)
        val tarjeta = LayoutInflater.from(ContextThemeWrapper(app, R.style.Tema)).inflate(R.layout.tarjeta_llamada, null)
        tarjeta.findViewById<TextView>(R.id.tarjeta_titulo).text = aviso.titulo
        tarjeta.findViewById<TextView>(R.id.tarjeta_numero).text = numero
        tarjeta.findViewById<TextView>(R.id.tarjeta_texto).text = aviso.texto
        tarjeta.findViewById<View>(R.id.tarjeta_franja).visibility = if (aviso.alto) View.VISIBLE else View.GONE
        tarjeta.findViewById<View>(R.id.tarjeta_cerrar).setOnClickListener { quitar(app) }
        // Tocar la tarjeta abre "¿Quién te llama?" con el número, igual que la notificación
        tarjeta.setOnClickListener {
            quitar(app)
            app.startActivity(
                Intent(app, MainActivity::class.java)
                    .putExtra(MainActivity.EXTRA_NUMERO, numero)
                    .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP),
            )
        }

        val margen = (16 * app.resources.displayMetrics.density).toInt()
        val parametros = WindowManager.LayoutParams(
            app.resources.displayMetrics.widthPixels - 2 * margen,
            WindowManager.LayoutParams.WRAP_CONTENT,
            WindowManager.LayoutParams.TYPE_APPLICATION_OVERLAY,
            // Sin tomar el teclado ni los toques fuera de la tarjeta: contestar y colgar siguen igual
            WindowManager.LayoutParams.FLAG_NOT_FOCUSABLE,
            PixelFormat.TRANSLUCENT,
        ).apply {
            gravity = Gravity.TOP or Gravity.CENTER_HORIZONTAL
            y = app.resources.displayMetrics.heightPixels / 4
        }
        try {
            ventanas.addView(tarjeta, parametros)
        } catch (e: RuntimeException) {
            return // sin permiso a última hora: queda la notificación
        }
        vista = tarjeta
        vigilarFin(app, System.currentTimeMillis(), vioLlamada = false)
    }

    private fun vigilarFin(app: Context, inicio: Long, vioLlamada: Boolean) {
        principal.postDelayed({
            if (vista == null) return@postDelayed
            val modo = app.getSystemService(AudioManager::class.java).mode
            val enLlamada = modo == AudioManager.MODE_RINGTONE || modo == AudioManager.MODE_IN_CALL ||
                modo == AudioManager.MODE_IN_COMMUNICATION ||
                (Build.VERSION.SDK_INT >= 30 && modo == AudioManager.MODE_CALL_SCREENING)
            val vio = vioLlamada || enLlamada
            if ((vio && !enLlamada) || System.currentTimeMillis() - inicio > MAXIMO) quitar(app)
            else vigilarFin(app, inicio, vio)
        }, REVISAR_CADA)
    }

    fun quitar(context: Context) {
        val actual = vista ?: return
        vista = null
        try {
            context.applicationContext.getSystemService(WindowManager::class.java).removeView(actual)
        } catch (_: IllegalArgumentException) {
        }
    }
}
