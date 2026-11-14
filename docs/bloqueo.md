# Bloqueo opcional de estafas confirmadas

En la app Android, *Ajustes > Rechazar llamadas de estafas confirmadas*. **Viene apagado**: un reporte puede estar equivocado, y la persona decide si prefiere no recibir esas llamadas. Sin encenderlo, Centinela nunca rechaza una llamada; a lo sumo avisa y, si se pidió, silencia el timbre.

## Qué rechaza

- Solo números en estado `estafa_confirmada` del [reporte de números](reportes.md): varias personas dicen que perdieron dinero o datos con ese número. Es el aviso "Probable estafa".
- Nunca "Posible estafa" (varios reportes sin pérdidas), un solo reporte, "Publicidad o call center", reportes que se contradicen ni reportes en revisión.
- Si el servidor no responde a tiempo, la llamada entra normal.
- Como todo el filtro de llamadas, Android solo le pasa a Centinela llamadas de números que no están en los contactos.

## Cómo se enciende

Al tocar el interruptor sale una confirmación: "Un reporte puede estar equivocado: si alguien que conoces llama desde un número reportado, su llamada no va a timbrar. Siempre puedes revisar las llamadas rechazadas y permitir el número." Si la persona cancela, queda apagado.

## Qué pasa con una llamada rechazada

- El teléfono no timbra. La llamada queda en el registro de llamadas del teléfono, como cualquier llamada rechazada.
- Centinela muestra una notificación: "Centinela rechazó una llamada de …", con la razón. Al tocarla se abren los ajustes en *Llamadas rechazadas*.
- El registro guarda las últimas 50, con número, aviso y hora, solo en el celular. Cada una tiene **Permitir este número**: desde ahí sus llamadas vuelven a entrar (con el aviso de siempre). *Borrar el registro* lo vacía.

## Para la demostración

Con `python sustentacion.py --demo`, el número 300 000 0001 queda como "Probable estafa". Con el bloqueo encendido, una llamada simulada desde ese número no timbra y llega la notificación de llamada rechazada; 300 000 0002 ("Posible estafa") sí timbra con su tarjeta. Así se muestra que el bloqueo solo actúa con estafas confirmadas.

## Por qué así

Android permite a las apps de filtro rechazar llamadas (`CallScreeningService`), y la Resolución 8308 de 2026 de la CRC ya obliga a los operadores a bloquear números irregulares (ver [denuncia](denuncia.md)). Centinela lo deja apagado y con registro porque su base es de reportes de la comunidad: un número suplantado o un reporte malintencionado no debe dejar sin llamadas a alguien sin que lo sepa y pueda corregirlo.
