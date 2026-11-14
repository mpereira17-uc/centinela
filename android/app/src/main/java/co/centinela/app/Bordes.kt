package co.centinela.app

import android.view.View
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat

/** Desde Android 15 la app ocupa toda la pantalla: se deja espacio para las barras del sistema y el teclado. */
fun View.respetarBarras() {
    ViewCompat.setOnApplyWindowInsetsListener(this) { vista, insets ->
        val b = insets.getInsets(WindowInsetsCompat.Type.systemBars() or WindowInsetsCompat.Type.ime())
        vista.setPadding(b.left, b.top, b.right, b.bottom)
        WindowInsetsCompat.CONSUMED
    }
}
