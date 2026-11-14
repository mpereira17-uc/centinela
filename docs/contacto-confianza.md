# Contacto de confianza

Pantalla **Ayuda > Contacto de confianza**. La persona escoge a alguien (un hijo, una vecina, un amigo) y su celular. Cuando un aviso llega a **riesgo crítico**, el aviso muestra un botón "Avisarle a …" que abre WhatsApp o los mensajes de texto con este texto listo:

> Hola Ana, Centinela marcó como posible estafa una llamada que estoy recibiendo. Te piden un código o una clave. ¿Me puedes llamar? No voy a dar códigos, claves ni plata.

## Decisiones

- **Nada se envía solo.** El botón usa `https://wa.me/57…?text=` o `sms:+57…?body=`; la persona ve el mensaje y decide si lo manda. En la beta web no hay otra forma, y además es lo correcto: un envío automático podría asustar a la familia por una falsa alarma.
- **Solo en crítico** (piden algo y presionan a la vez), para no gastar la confianza del contacto en avisos menores.
- **El texto no lleva la conversación**: solo el motivo general del aviso (por ejemplo, "te piden un código"). Así no se comparte lo que dijo quien llama ni datos de la persona.
- **Datos de un tercero (Ley 1581 de 2012):** el nombre y el celular quedan solo en el navegador (`localStorage`, `centinela-contacto`), nunca en el servidor. Para guardarlo hay que marcar "Le pregunté a esta persona y está de acuerdo". Se puede quitar en cualquier momento.
- Solo se aceptan celulares colombianos de 10 dígitos que empiezan por 3, con o sin +57.
- Hay un enlace "Enviarle un mensaje de prueba" para que la persona practique el gesto antes de necesitarlo.

## En la app Android

El aviso de una llamada con varios reportes de estafa ("Posible estafa" o "Probable estafa") trae un botón **Llamar a …** con el contacto guardado. Abre el marcador del celular con el número escrito y la persona toca llamar: la app no pide permiso de llamadas ni llama sola. Así la persona puede no contestar, o colgar, y preguntarle a alguien de confianza antes de hacer nada.

- La página le pasa el nombre y el número a la app por un canal que solo existe dentro de la app y solo para la dirección del servidor configurado (`CentinelaApp`, con `WebViewCompat.addWebMessageListener`). La app vuelve a validar el celular y recorta el nombre a 30 caracteres.
- Quedan en las preferencias privadas de la app (sin copia de seguridad en la nube) y se borran al tocar **Quitar** en la página.
- Avisarle al contacto con una notificación en su propio celular necesitaría un servidor de notificaciones y el consentimiento de los dos; queda para después de la beta.
