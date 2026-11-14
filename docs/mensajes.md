# Revisar un mensaje

Muchas estafas empiezan con un SMS, un WhatsApp o un correo: "su paquete está retenido, pague el envío aquí", "su cuenta fue bloqueada, ingrese a...". La tarjeta **Revisar un mensaje** de la pantalla principal analiza el texto pegado con el mismo motor de señales de las llamadas y le suma la revisión de los enlaces.

## Qué revisa de cada enlace

Centinela **nunca abre el enlace**. Solo mira cómo está escrito:

| Hallazgo | Ejemplo | Señal |
|---|---|---|
| Usa el nombre de una entidad pero no es su dominio oficial (también con números en lugar de letras) | `bancolombia-seguridad.xyz`, `d4vivienda.co` | `enlace_suplanta` (solicitud) |
| Enlace acortado | `bit.ly/...` | `enlace_sospechoso` (contexto) |
| Dirección numérica | `http://192.168.1.10/pago` | `enlace_sospechoso` |
| Letras de otros alfabetos (punycode) | `xn--bncolombia-...` | `enlace_sospechoso` |
| Destino escondido detrás de una @ | `google.com@estafa.com` | `enlace_sospechoso` |
| Terminación muy usada en engaños | `.xyz`, `.click`, `.online` | `enlace_sospechoso` |

Si además el mensaje pide entrar, pagar, actualizar, reclamar o confirmar y el enlace no es oficial, se suma `pide_entrar_enlace` (solicitud). Los dominios oficiales están en [backend/app/enlaces.py](../backend/app/enlaces.py) y cualquier `.gov.co` cuenta como oficial.

Los niveles se calculan con las mismas reglas de siempre ([motor de señales](motor-de-senales.md)): un enlace que imita a una entidad lleva a **alto**, y con afán o amenaza a **crítico**.

## Para no alarmar con mensajes normales

- "Nequi: recibiste 50.000" no es un pedido de plata: en los mensajes, el nombre de la billetera no cuenta como transferencia.
- "Tu clave dinámica es 123456. No la compartas" entrega un código, no lo pide. Sí se marca si además pide reenviarlo ("envíela a este número").
- Un enlace a una página oficial se muestra como "página oficial".

## Compartir con Centinela

En vez de copiar y pegar, la persona mantiene presionado el mensaje en WhatsApp o en Mensajes, busca la opción **Compartir** y elige Centinela. Dónde está esa opción cambia según la app y su versión; si no aparece, copiar y pegar sigue sirviendo. Se abre **Revisar un mensaje** con el texto puesto y la revisión empieza sola; la respuesta queda a la vista.

- **App de Android:** la app recibe el texto compartido (`ACTION_SEND`, `text/plain`) y abre `/?compartido=app#mensaje`. La página le pide el texto por el canal `CentinelaApp`, que solo existe dentro de la app y para el servidor configurado, y la app se lo entrega una sola vez.
- **App instalable (PWA):** el manifiesto declara un destino para compartir (`share_target`) por POST. El service worker guarda el texto un momento en el celular, abre `/?compartido=1#mensaje` y la página lo lee y lo borra. Si el service worker no está activo, el servidor responde `/compartir` sin leer el texto y la página pide pegarlo.
- El mensaje nunca va en la dirección de la página, así no queda en el historial ni en los registros del servidor. Solo sale del celular cuando se revisa, igual que al pegarlo.
- Se recortan los mismos 2000 caracteres del campo. Si el enlace compartido ya está dentro del texto, no se repite.
- Quien llega compartiendo un mensaje o desde el aviso de una llamada no ve la bienvenida; se muestra la próxima vez que abra la app.

## Límites

- Sin abrir el enlace no se sabe si la página es nueva, si ya la bloquearon ni qué contiene. Un enlace sin hallazgos no es garantía; la pantalla lo dice.
- La lista de dominios oficiales es corta y hay que mantenerla. Una entidad que no esté en la lista no se reconoce como imitada.
- El mensaje no se guarda ni se escribe en los logs.
