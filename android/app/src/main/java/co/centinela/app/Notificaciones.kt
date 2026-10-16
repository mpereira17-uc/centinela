package co.centinela.app

import android.Manifest
import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.app.PendingIntent
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.drawable.Icon
import android.net.Uri
import android.os.Build

object Notificaciones {
    private const val CANAL = "llamadas"

    fun crearCanal(context: Context) {
        val canal = NotificationChannel(CANAL, "Avisos de llamadas", NotificationManager.IMPORTANCE_HIGH).apply {
            description = "Aparece cuando te llama un número que otras personas reportaron en Centinela."
        }
        context.getSystemService(NotificationManager::class.java).createNotificationChannel(canal)
    }

    fun mostrar(context: Context, numero: String, aviso: Aviso) {
        if (Build.VERSION.SDK_INT >= 33 &&
            context.checkSelfPermission(Manifest.permission.POST_NOTIFICATIONS) != PackageManager.PERMISSION_GRANTED
        ) return
        crearCanal(context)
        // Al tocarlo se abre "¿Quién te llama?" con el número, para consultarlo o reportarlo al colgar
        val abrir = Intent(context, MainActivity::class.java)
            .putExtra(MainActivity.EXTRA_NUMERO, numero)
            .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TOP)
        val alTocar = PendingIntent.getActivity(
            context, numero.hashCode(), abrir, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
        )
        val notificacion = Notification.Builder(context, CANAL)
            .setSmallIcon(R.drawable.ic_buho)
            .setColor(context.getColor(R.color.ambar))
            .setContentTitle("${aviso.titulo}: $numero")
            .setContentText(aviso.texto)
            .setStyle(Notification.BigTextStyle().bigText("${aviso.texto}\n\nAl colgar, toca aquí para contar cómo terminó o reportar el número."))
            .setContentIntent(alTocar)
            .setAutoCancel(true)
        // Con varios reportes de estafa y un contacto de confianza guardado: un botón para llamarle y preguntar.
        // Abre el marcador con el número escrito; la persona toca llamar (la app no pide permiso de llamadas).
        val contacto = Ajustes(context).contacto
        if (aviso.alto && contacto != null) {
            val marcar = Intent(Intent.ACTION_DIAL, Uri.parse("tel:+57${contacto.telefono}"))
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            val alLlamar = PendingIntent.getActivity(
                context, numero.hashCode() + 1, marcar, PendingIntent.FLAG_IMMUTABLE or PendingIntent.FLAG_UPDATE_CURRENT,
            )
            notificacion.addAction(
                Notification.Action.Builder(Icon.createWithResource(context, R.drawable.ic_buho), Contactos.textoLlamar(contacto), alLlamar)
                    .build(),
            )
        }
        context.getSystemService(NotificationManager::class.java).notify(numero.hashCode(), notificacion.build())
    }
}
