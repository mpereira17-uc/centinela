# Me estafaron, ¿qué hago?

Sección de la pantalla **Ayuda** (`/ayuda.html#me-estafaron`), también en los accesos rápidos de la pantalla principal. Es la "respuesta ante incidentes" de la [especificación](especificacion.md) (sección 11).

La persona marca lo que pasó y la app muestra los pasos en orden de urgencia:

| Si... | Pasos |
|---|---|
| Lo están amenazando o extorsionando | No pagar, guardar evidencia y llamar al 165 (GAULA) |
| Dio un código, la clave o la tarjeta, o envió plata | Llamar ya al banco por el número del respaldo de la tarjeta o de la app oficial; pedir bloqueo y preguntar si se puede detener o reversar |
| Envió por una billetera | Reportarlo dentro de la app oficial, con hora, valor y destino |
| Instaló una aplicación | Desconectar internet y desinstalarla antes de abrir el banco |
| Dio el código de WhatsApp | Volver a registrar el número, activar la verificación en dos pasos y avisar a los contactos |
| Cualquiera de las anteriores | Cambiar claves desde un equipo seguro, denunciar (con el [resumen para la denuncia](denuncia.md)), reportar el número en Centinela y contárselo a alguien de confianza |
| Dio la cédula u otros datos | Revisar las centrales de riesgo por si abren créditos a su nombre |

El último paso advierte la "estafa de recuperación": alguien llama fingiendo ser la policía o el banco para cobrar por recuperar la plata.

## Cuidados

- El texto empieza con "no es tu culpa": quien acaba de perder plata necesita instrucciones claras, no reproches.
- La app no promete recuperar el dinero ni dice que el banco está obligado a devolverlo; solo indica preguntar si la operación se puede detener o reversar.
- Los pasos marcados como hechos se guardan solo en el navegador (`localStorage`), no en el servidor.
