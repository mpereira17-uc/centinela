package co.centinela.app

import android.Manifest
import android.app.AlertDialog
import android.app.role.RoleManager
import android.content.Intent
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.provider.Settings
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.Switch
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts
import java.text.DateFormat
import java.util.Date
import java.util.Locale

/**
 * Ajustes nativos: la dirección del servidor, activar el filtro de llamadas, la tarjeta sobre la
 * pantalla de llamada, el aviso hablado, silenciar el timbre de los números con muchos reportes y el
 * bloqueo opcional de estafas confirmadas, con su registro de llamadas rechazadas.
 *
 * El enlace centinela://configurar?servidor=… (desde la página de instalar) solo llena el campo:
 * la persona debe tocar Guardar, para que ninguna página pueda cambiar a escondidas a dónde van los números.
 */
class AjustesActivity : ComponentActivity() {
    companion object {
        const val EXTRA_SIN_CONEXION = "sin_conexion"
        const val EXTRA_RECHAZADAS = "rechazadas"
    }

    private lateinit var ajustes: Ajustes
    private lateinit var roles: RoleManager

    private val pedirFiltro = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { pintar() }
    private val pedirTarjeta = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { pintar() }
    private val pedirNotificaciones = registerForActivityResult(ActivityResultContracts.RequestPermission()) { pintar() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.ajustes)
        findViewById<View>(R.id.raiz).respetarBarras()
        ajustes = Ajustes(this)
        ajustes.ajustesVistos = true
        roles = getSystemService(RoleManager::class.java)
        Notificaciones.crearCanal(this)

        val campo = findViewById<EditText>(R.id.servidor)
        campo.setText(intent.data?.getQueryParameter("servidor") ?: ajustes.servidor)
        if (intent.getBooleanExtra(EXTRA_SIN_CONEXION, false)) campo.error = getString(R.string.servidor_sin_conexion)

        findViewById<Button>(R.id.guardar).setOnClickListener {
            val direccion = Direcciones.normalizar(campo.text.toString())
            if (direccion == null) {
                campo.error = getString(R.string.servidor_invalido)
            } else {
                ajustes.servidor = direccion
                campo.setText(direccion)
                pintar()
            }
        }
        findViewById<Button>(R.id.activar_filtro).setOnClickListener {
            if (Build.VERSION.SDK_INT >= 33) pedirNotificaciones.launch(Manifest.permission.POST_NOTIFICATIONS)
            pedirFiltro.launch(roles.createRequestRoleIntent(RoleManager.ROLE_CALL_SCREENING))
        }
        findViewById<Button>(R.id.activar_tarjeta).setOnClickListener {
            pedirTarjeta.launch(Intent(Settings.ACTION_MANAGE_OVERLAY_PERMISSION, Uri.parse("package:$packageName")))
        }
        findViewById<Switch>(R.id.silenciar).apply {
            isChecked = ajustes.silenciarRiesgoAlto
            setOnCheckedChangeListener { _, activo -> ajustes.silenciarRiesgoAlto = activo }
        }
        findViewById<Switch>(R.id.bloquear).apply {
            // El estado sale siempre de los ajustes, no del que Android restaura al girar la pantalla
            isSaveEnabled = false
            isChecked = ajustes.bloquearConfirmadas
            setOnCheckedChangeListener { boton, activo ->
                if (activo && !ajustes.bloquearConfirmadas) confirmarBloqueo(boton as Switch)
                else if (!activo) {
                    ajustes.bloquearConfirmadas = false
                    pintar()
                }
            }
        }
        findViewById<Button>(R.id.borrar_rechazadas).setOnClickListener {
            ajustes.rechazadas = emptyList()
            pintar()
        }
        findViewById<Switch>(R.id.aviso_hablado).apply {
            isChecked = ajustes.avisoHablado
            setOnCheckedChangeListener { _, activo -> ajustes.avisoHablado = activo }
        }
        findViewById<Button>(R.id.abrir).setOnClickListener {
            startActivity(Intent(this, MainActivity::class.java))
            finish()
        }
        pintar()
        // Desde la notificación de una llamada rechazada: directo al registro
        if (intent.getBooleanExtra(EXTRA_RECHAZADAS, false)) {
            val raiz = findViewById<ScrollView>(R.id.raiz)
            val seccion = findViewById<View>(R.id.seccion_rechazadas)
            raiz.post { raiz.smoothScrollTo(0, seccion.top) }
        }
    }

    override fun onResume() {
        super.onResume()
        pintar()
    }

    // Encender el bloqueo pide confirmar, porque un reporte equivocado deja sin timbrar a alguien conocido
    private fun confirmarBloqueo(boton: Switch) {
        AlertDialog.Builder(this)
            .setTitle(R.string.bloquear_confirmar_titulo)
            .setMessage(R.string.bloquear_confirmar)
            .setPositiveButton(R.string.bloquear_si) { _, _ ->
                ajustes.bloquearConfirmadas = true
                pintar()
            }
            .setNegativeButton(R.string.cancelar, null)
            .setOnDismissListener { if (!ajustes.bloquearConfirmadas) boton.isChecked = false }
            .show()
    }

    private fun pintarRechazadas() {
        val registro = ajustes.rechazadas
        val permitidos = ajustes.permitidos
        findViewById<View>(R.id.seccion_rechazadas).visibility =
            if (ajustes.bloquearConfirmadas || registro.isNotEmpty()) View.VISIBLE else View.GONE
        findViewById<View>(R.id.rechazadas_vacio).visibility = if (registro.isEmpty()) View.VISIBLE else View.GONE
        findViewById<View>(R.id.borrar_rechazadas).visibility = if (registro.isEmpty()) View.GONE else View.VISIBLE
        val formato = DateFormat.getDateTimeInstance(DateFormat.MEDIUM, DateFormat.SHORT, Locale.forLanguageTag("es-CO"))
        val lista = findViewById<LinearLayout>(R.id.lista_rechazadas)
        lista.removeAllViews()
        // Los márgenes del estilo no aplican a vistas creadas en código; se ponen aquí
        fun conMargen(dp: Int) = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
            .apply { topMargin = (dp * resources.displayMetrics.density).toInt() }
        for (llamada in registro) {
            val fila = TextView(this, null, 0, R.style.Texto).apply {
                text = "${llamada.numero}\n${llamada.titulo} · ${formato.format(Date(llamada.fecha))}"
            }
            lista.addView(fila, conMargen(16))
            if (Bloqueo.clave(llamada.numero) in permitidos) {
                lista.addView(TextView(this, null, 0, R.style.Ayuda).apply { setText(R.string.permitido) }, conMargen(4))
            } else {
                val permitir = Button(this, null, 0, R.style.Boton).apply {
                    setText(R.string.permitir)
                    setOnClickListener {
                        ajustes.permitir(llamada.numero)
                        pintar()
                    }
                }
                lista.addView(permitir, conMargen(8))
            }
        }
    }

    private fun pintar() {
        val hayServidor = ajustes.servidor.isNotBlank()
        val disponible = roles.isRoleAvailable(RoleManager.ROLE_CALL_SCREENING)
        val activo = roles.isRoleHeld(RoleManager.ROLE_CALL_SCREENING)
        findViewById<TextView>(R.id.estado_filtro).text = getString(
            when {
                !disponible -> R.string.filtro_no_disponible
                activo -> R.string.filtro_activo
                else -> R.string.filtro_inactivo
            },
        )
        findViewById<Button>(R.id.activar_filtro).visibility = if (disponible && !activo) View.VISIBLE else View.GONE
        val tarjeta = TarjetaLlamada.puedeMostrarse(this)
        findViewById<TextView>(R.id.estado_tarjeta).text = getString(if (tarjeta) R.string.tarjeta_activa else R.string.tarjeta_inactiva)
        findViewById<Button>(R.id.activar_tarjeta).visibility = if (tarjeta) View.GONE else View.VISIBLE
        findViewById<Button>(R.id.abrir).isEnabled = hayServidor
        pintarRechazadas()
    }
}
