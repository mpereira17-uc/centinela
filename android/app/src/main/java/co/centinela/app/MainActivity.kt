package co.centinela.app

import android.Manifest
import android.annotation.SuppressLint
import android.app.role.RoleManager
import android.content.ActivityNotFoundException
import android.content.Intent
import android.content.pm.PackageManager
import android.net.Uri
import android.os.Bundle
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebResourceResponse
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.activity.ComponentActivity
import androidx.activity.addCallback
import androidx.activity.result.contract.ActivityResultContracts

/**
 * La app es la misma interfaz web de Centinela dentro de un WebView, más lo que solo una app nativa
 * puede hacer: el filtro de llamadas ([FiltroLlamadas]) y sus avisos.
 */
class MainActivity : ComponentActivity() {
    companion object {
        const val EXTRA_NUMERO = "numero"
    }

    private lateinit var web: WebView
    private lateinit var servidor: String
    private var permisoPendiente: PermissionRequest? = null

    private val pedirMicrofono = registerForActivityResult(ActivityResultContracts.RequestPermission()) { concedido ->
        permisoPendiente?.let { if (concedido) it.grant(arrayOf(PermissionRequest.RESOURCE_AUDIO_CAPTURE)) else it.deny() }
        permisoPendiente = null
    }

    @SuppressLint("SetJavaScriptEnabled")
    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val ajustes = Ajustes(this)
        servidor = ajustes.servidor
        // Sin servidor, o la primera vez si el filtro de llamadas no está activo, se abren los ajustes
        val filtroActivo = getSystemService(RoleManager::class.java).isRoleHeld(RoleManager.ROLE_CALL_SCREENING)
        if (servidor.isBlank() || (!filtroActivo && !ajustes.ajustesVistos)) {
            startActivity(Intent(this, AjustesActivity::class.java))
            finish()
            return
        }

        web = WebView(this)
        web.setBackgroundColor(getColor(R.color.marino))
        web.respetarBarras()
        setContentView(web)
        web.settings.apply {
            javaScriptEnabled = true
            domStorageEnabled = true
            mediaPlaybackRequiresUserGesture = false
        }
        web.webViewClient = object : WebViewClient() {
            override fun shouldOverrideUrlLoading(view: WebView, request: WebResourceRequest): Boolean {
                val url = request.url
                if (esDelServidor(url)) return false
                // Enlaces de afuera (WhatsApp, llamar a la entidad, la Fiscalía) se abren en su app
                val intento = if (url.scheme == "centinela") Intent(this@MainActivity, AjustesActivity::class.java).setData(url)
                else Intent(Intent.ACTION_VIEW, url)
                try {
                    startActivity(intento)
                } catch (e: ActivityNotFoundException) {
                    // nada que abra ese enlace
                }
                return true
            }

            // Si el servidor no responde (por ejemplo, se reinició y su dirección cambió), se vuelve a Ajustes
            override fun onReceivedError(view: WebView, request: WebResourceRequest, error: WebResourceError) {
                if (request.isForMainFrame) volverAAjustes()
            }

            override fun onReceivedHttpError(view: WebView, request: WebResourceRequest, respuesta: WebResourceResponse) {
                if (request.isForMainFrame && respuesta.statusCode >= 500) volverAAjustes()
            }
        }
        web.webChromeClient = object : WebChromeClient() {
            override fun onPermissionRequest(request: PermissionRequest) {
                // Solo el micrófono y solo para el servidor configurado (modo acompañante, llamada, asistente)
                if (!esDelServidor(request.origin) || PermissionRequest.RESOURCE_AUDIO_CAPTURE !in request.resources) {
                    request.deny()
                } else if (checkSelfPermission(Manifest.permission.RECORD_AUDIO) == PackageManager.PERMISSION_GRANTED) {
                    request.grant(arrayOf(PermissionRequest.RESOURCE_AUDIO_CAPTURE))
                } else {
                    permisoPendiente = request
                    pedirMicrofono.launch(Manifest.permission.RECORD_AUDIO)
                }
            }
        }
        onBackPressedDispatcher.addCallback(this) {
            if (web.canGoBack()) web.goBack() else finish()
        }
        if (savedInstanceState != null) web.restoreState(savedInstanceState) else web.loadUrl(direccion(intent))
    }

    override fun onNewIntent(intent: Intent) {
        super.onNewIntent(intent)
        setIntent(intent)
        if (::web.isInitialized && intent.hasExtra(EXTRA_NUMERO)) web.loadUrl(direccion(intent))
    }

    override fun onSaveInstanceState(outState: Bundle) {
        super.onSaveInstanceState(outState)
        if (::web.isInitialized) web.saveState(outState)
    }

    private fun volverAAjustes() {
        if (isFinishing) return
        startActivity(Intent(this, AjustesActivity::class.java).putExtra(AjustesActivity.EXTRA_SIN_CONEXION, true))
        finish()
    }

    private fun esDelServidor(url: Uri): Boolean {
        val base = Uri.parse(servidor)
        return url.scheme == "https" && url.host == base.host && url.port == base.port
    }

    private fun direccion(intent: Intent): String {
        val numero = intent.getStringExtra(EXTRA_NUMERO) ?: return "$servidor/"
        return "$servidor/?numero=${Uri.encode(numero)}#numero-titulo"
    }
}
