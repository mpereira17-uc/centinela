package co.centinela.app

import android.Manifest
import android.app.role.RoleManager
import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.Button
import android.widget.EditText
import android.widget.Switch
import android.widget.TextView
import androidx.activity.ComponentActivity
import androidx.activity.result.contract.ActivityResultContracts

/**
 * Ajustes nativos: la dirección del servidor, activar el filtro de llamadas y silenciar el timbre
 * de los números con muchos reportes.
 *
 * El enlace centinela://configurar?servidor=… (desde la página de instalar) solo llena el campo:
 * la persona debe tocar Guardar, para que ninguna página pueda cambiar a escondidas a dónde van los números.
 */
class AjustesActivity : ComponentActivity() {
    private lateinit var ajustes: Ajustes
    private lateinit var roles: RoleManager

    private val pedirFiltro = registerForActivityResult(ActivityResultContracts.StartActivityForResult()) { pintar() }
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
        findViewById<Switch>(R.id.silenciar).apply {
            isChecked = ajustes.silenciarRiesgoAlto
            setOnCheckedChangeListener { _, activo -> ajustes.silenciarRiesgoAlto = activo }
        }
        findViewById<Button>(R.id.abrir).setOnClickListener {
            startActivity(Intent(this, MainActivity::class.java))
            finish()
        }
        pintar()
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
        findViewById<Button>(R.id.abrir).isEnabled = hayServidor
    }
}
