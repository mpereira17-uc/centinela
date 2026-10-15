# ¿Cómo terminó? Feedback de un toque al colgar

Al colgar la [llamada de prueba](llamada.md), quien recibió la llamada ve tres botones: **Me estafaron**, **Intentaron estafarme** y **Era una llamada normal**, más un enlace para **Era publicidad o un call center**. Es el feedback de la llamada en vivo, la fuente que más ayuda a separar estafas de llamadas normales.

## Qué pasa con la respuesta

1. **Se cuenta para medir a Centinela** (`POST /llamadas/{id}/desenlace`). Se guarda solo el nivel máximo que vio la persona, si hubo aviso y lo que contó. No se guarda la cuenta, el número ni el texto. Se pregunta una vez por llamada.
2. **Si la persona escribió el número al empezar y tiene cuenta, también queda como reporte del número**, respaldado por el análisis de esa llamada si Centinela marcó alto o crítico ([reportes](reportes.md)). La categoría ("se hizo pasar por un banco", "extorsión"...) se deduce de las señales detectadas, para que sea un solo toque. Sin cuenta, la app invita a entrar.
3. **Si la persona perdió algo**, la app la lleva a la guía [Me estafaron, ¿qué hago?](me-estafaron.md).

## Resumen para el informe

`GET /desenlaces/resumen` devuelve la tabla de aciertos con lo que contaron las personas:

| | Estafa (perdida o intento) | No estafa (normal o publicidad) |
|---|---|---|
| Hubo aviso | acierto | falsa alarma |
| No hubo aviso | estafa no avisada | acierto |

Con las llamadas del piloto en Bogotá, estas cifras son la medición fuera del laboratorio que los guiones no pueden dar. Hay que leerlas con cuidado: lo cuenta cada persona y no está verificado, y quien colgó sin responder no aparece.
