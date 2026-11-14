package co.centinela.app

import android.app.NotificationManager
import android.content.Context
import android.media.AudioAttributes
import android.media.AudioManager
import android.os.Build
import android.os.Handler
import android.os.Looper
import android.os.VibrationAttributes
import android.os.VibrationEffect
import android.os.Vibrator
import android.os.VibratorManager
import android.speech.tts.TextToSpeech
import java.util.Locale

/**
 * Aviso hablado y vibración propia mientras timbra un número con varios reportes de estafa, para quien
 * no alcanza a leer la tarjeta: el celular dice "Cuidado: posible estafa…" y vibra con tres toques cortos.
 *
 * Respeta el silencio de la persona: nada suena en modo silencio ni en No molestar, ni si pidió silenciar
 * esos números; en modo vibración solo vibra. Se calla en cuanto se contesta o se cuelga, igual que la
 * tarjeta, mirando el modo de audio (no pide permiso de llamadas).
 */
object AvisoHablado {
    enum class Modo { NADA, VIBRAR, HABLAR_Y_VIBRAR }

    private val principal = Handler(Looper.getMainLooper())
    private var voz: TextToSpeech? = null
    private var vibrador: Vibrator? = null
    // Cada aviso tiene su turno; lo que quede pendiente de un aviso anterior se ignora
    private var turno = 0
    private const val REVISAR_CADA = 500L
    // El filtro responde antes de que empiece el timbre; si no empieza en este tiempo, no se dice nada
    private const val ESPERA_TIMBRE = 5_000L
    private const val MAXIMO = 60_000L
    // Tres toques cortos y una pausa, distinto de la vibración normal de una llamada
    private val PATRON = longArrayOf(0, 160, 110, 160, 110, 160, 900)

    /** Lo que se dice: corto, sin el número (se ve en pantalla) y con lo que hay que hacer si se contesta. */
    fun frase(aviso: Aviso) =
        "Cuidado: ${aviso.titulo.lowercase(Locale.ROOT)}. Varias personas de Centinela reportaron este número. " +
            "Si contestas, no des códigos, claves ni plata."

    fun modo(aviso: Aviso, activado: Boolean, timbre: Int, noMolestar: Boolean): Modo = when {
        !aviso.alto || !activado || aviso.silenciar || noMolestar -> Modo.NADA
        timbre == AudioManager.RINGER_MODE_NORMAL -> Modo.HABLAR_Y_VIBRAR
        timbre == AudioManager.RINGER_MODE_VIBRATE -> Modo.VIBRAR
        else -> Modo.NADA
    }

    fun iniciar(context: Context, aviso: Aviso, activado: Boolean) {
        val app = context.applicationContext
        val filtro = app.getSystemService(NotificationManager::class.java).currentInterruptionFilter
        val noMolestar = filtro != NotificationManager.INTERRUPTION_FILTER_ALL &&
            filtro != NotificationManager.INTERRUPTION_FILTER_UNKNOWN
        val modo = modo(aviso, activado, app.getSystemService(AudioManager::class.java).ringerMode, noMolestar)
        if (modo == Modo.NADA) return
        principal.post { empezar(app, aviso, modo) }
    }

    /** Se calla y deja de vibrar. Lo llama también la tarjeta al cerrarla o tocarla. */
    fun detener() {
        if (Looper.myLooper() != Looper.getMainLooper()) {
            principal.post { detener() }
            return
        }
        turno++
        voz?.let {
            it.stop()
            it.shutdown()
        }
        voz = null
        vibrador?.cancel()
        vibrador = null
    }

    private fun empezar(app: Context, aviso: Aviso, modo: Modo) {
        detener()
        val mio = turno
        if (modo == Modo.HABLAR_Y_VIBRAR) {
            // La voz se prepara mientras empieza el timbre; se habla en vigilar(), cuando ya timbra
            voz = TextToSpeech(app) { estado -> if (estado != TextToSpeech.SUCCESS && mio == turno) voz = null }
        }
        vigilar(app, aviso, mio, System.currentTimeMillis(), vecesTimbrando = 0, hablo = false)
    }

    private fun vigilar(app: Context, aviso: Aviso, mio: Int, inicio: Long, vecesTimbrando: Int, hablo: Boolean) {
        principal.postDelayed({
            if (mio != turno) return@postDelayed
            val timbrando = app.getSystemService(AudioManager::class.java).mode == AudioManager.MODE_RINGTONE
            val transcurrido = System.currentTimeMillis() - inicio
            val termino = (vecesTimbrando > 0 && !timbrando) || (vecesTimbrando == 0 && transcurrido > ESPERA_TIMBRE) ||
                transcurrido > MAXIMO
            if (termino) {
                detener()
                return@postDelayed
            }
            val veces = if (timbrando) vecesTimbrando + 1 else vecesTimbrando
            // La vibración del teléfono arranca un instante después del timbre; la propia va después para no ser reemplazada
            if (veces == 2) vibrar(app)
            val ahoraHabla = !hablo && timbrando && hablar(aviso)
            vigilar(app, aviso, mio, inicio, veces, hablo || ahoraHabla)
        }, REVISAR_CADA)
    }

    /** Devuelve true si empezó a hablar; si la voz aún no está lista, se intenta en la siguiente revisión. */
    private fun hablar(aviso: Aviso): Boolean {
        val v = voz ?: return false
        // Sin voz en español no se dice nada: un aviso en otro idioma confunde más de lo que ayuda
        val idioma = listOf("es-CO", "es-US", "es-419", "es").map(Locale::forLanguageTag)
            .firstOrNull { v.isLanguageAvailable(it) >= TextToSpeech.LANG_AVAILABLE }
        if (idioma == null) {
            // isLanguageAvailable da error mientras la voz no termina de cargar
            return false
        }
        v.language = idioma
        // Con el uso de timbre suena al volumen de las llamadas, no al de la música
        v.setAudioAttributes(
            AudioAttributes.Builder()
                .setUsage(AudioAttributes.USAGE_NOTIFICATION_RINGTONE)
                .setContentType(AudioAttributes.CONTENT_TYPE_SPEECH)
                .build(),
        )
        v.setSpeechRate(0.9f)
        val texto = frase(aviso)
        v.speak(texto, TextToSpeech.QUEUE_FLUSH, null, "aviso")
        v.playSilentUtterance(1_500, TextToSpeech.QUEUE_ADD, "pausa")
        v.speak(texto, TextToSpeech.QUEUE_ADD, null, "aviso-repetido")
        return true
    }

    private fun vibrar(app: Context) {
        val v = if (Build.VERSION.SDK_INT >= 31) {
            app.getSystemService(VibratorManager::class.java).defaultVibrator
        } else {
            app.getSystemService(Vibrator::class.java)
        }
        if (v == null || !v.hasVibrator()) return
        // Se repite como la de una llamada y reemplaza la del teléfono mientras timbra; se cancela al terminar
        val efecto = VibrationEffect.createWaveform(PATRON, 0)
        if (Build.VERSION.SDK_INT >= 33) {
            v.vibrate(efecto, VibrationAttributes.createForUsage(VibrationAttributes.USAGE_RINGTONE))
        } else {
            @Suppress("DEPRECATION")
            v.vibrate(efecto, AudioAttributes.Builder().setUsage(AudioAttributes.USAGE_NOTIFICATION_RINGTONE).build())
        }
        vibrador = v
    }
}
