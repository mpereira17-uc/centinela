# Reporte de números

Paso 8 de la [hoja de ruta](hoja-de-ruta.md). Quien recibe una llamada puede escribir el número que lo llama, consultar si otras personas lo reportaron y reportarlo si intentaron estafarlo.

![Número reportado en el celular](capturas/reportes-movil.png)

## Reglas

| Regla | Por qué (modelo de amenazas) |
|---|---|
| Reportar exige cuenta; consultar no | Frena reportes falsos en masa sin impedir que cualquiera se proteja (A15) |
| Cada cuenta reporta un número una sola vez, en cualquier formato | `300 123 4567`, `+57 300-123-4567` y `3001234567` son el mismo número (A15) |
| Máximo 10 reportes por cuenta al día | Limita a quien quiera perjudicar a muchos números (A15) |
| Solo cuentan los reportes de los últimos 180 días | Los números cambian de dueño |
| La consulta dice cuántas personas reportaron, nunca quiénes | Reportes seudónimos (A16) |
| "Reportado" no es "confirmado" | El texto siempre aclara que un reporte no confirma la estafa (A15) |
| Consultar está limitado a 30 por minuto por IP | Evita recorrer números en masa (A6) |

## Reputación comunitaria

Como en las apps de identificación de llamadas, la comunidad avisa antes de contestar. Para que avise sobre estafas reales y no sobre un call center molesto, ni por una campaña de odio contra un número, cada reporte dice qué pasó y tiene un peso.

| Qué pasó | Peso | Cuenta como |
|---|---|---|
| Me estafaron: perdí dinero, datos o el control de una cuenta | 1,5 | Estafa |
| Intentaron estafarme, pero no caí | 1,0 | Estafa |
| Era publicidad, cobranza o un call center | 1,0 | Publicidad, aparte |
| Era una llamada legítima | 1,0 | En contra de la estafa |

Ajustes al peso, en contra del abuso (A22):

- **Cuentas nuevas:** un reporte hecho con una cuenta de menos de un día no cuenta hasta que la cuenta cumple el día.
- **Avalanchas:** por número, solo cuentan los primeros 3 reportes de cada día; los demás quedan en espera.
- **Respaldo:** si el reporte viene de una conversación sobre ese mismo número que Centinela marcó alto o crítico, pesa ×1,5.
- **Antigüedad:** el peso se reduce a la mitad cada 90 días y a los 180 deja de contar, porque los números cambian de dueño.

Con la suma se decide el estado que ve quien consulta:

| Estado | Cuándo | ¿Señal en el análisis? |
|---|---|---|
| `sin_reportes` | Nadie ha reportado | No |
| `en_revision` | Solo hay reportes que todavía no cuentan | No |
| `reportado` | Puntaje de estafa menor que 2 | No |
| `varios_reportes` | Puntaje de estafa de 2 o más | Sí |
| `estafa_confirmada` | Puntaje de 3 o más y al menos 2 personas que perdieron algo | Sí |
| `publicidad` | Pesa más "publicidad" que "estafa" | No |
| `en_disputa` | Lo legítimo pesa al menos la mitad que lo de estafa | No |

"Confirmada" quiere decir confirmada por personas de la comunidad que dicen haber perdido algo, no por una entidad; el mensaje lo dice así.

## Cómo pesa en el análisis

En los estados con señal, cada decisión suma la señal de contexto `numero_reportado` y marca `fuente: "contenido_y_reputacion"`. Por las reglas del [motor de señales](motor-de-senales.md):

- Sola, la señal deja la llamada en **moderado** y no dispara la alerta.
- Junto con otras dos señales de contexto o presión suma tres señales: **alto**.
- Con una solicitud sensible el nivel ya era alto o crítico por el contenido.

Así un número con mala reputación pone a la persona en guardia, pero la alerta fuerte sigue dependiendo de lo que le piden en la llamada.

## Qué se guarda

| Dato | Cómo |
|---|---|
| Número | HMAC-SHA256 con una clave aleatoria guardada en la base local. Sin la clave no se puede saber qué números hay |
| Últimos 4 dígitos | Para que quien reportó reconozca su reporte en "Mi cuenta" |
| Qué pasó y motivo | Uno de cuatro resultados y una de seis categorías cerradas, sin texto libre |
| Respaldo | Si el reporte vino de una conversación analizada; la conversación no se guarda en el reporte |
| Autor | El identificador interno de la cuenta, que nunca sale en la consulta |

La llamada en memoria guarda la reputación y la referencia HMAC del número (para comprobar el respaldo), no el número. La consulta usa `POST` para que el número no quede en los registros de acceso del servidor, y los logs registran solo identificadores y categorías.

Quien reportó puede ver sus reportes y retirarlos en "Mi cuenta". Eliminar la cuenta retira todos sus reportes, y la exportación de datos los incluye con sus últimos 4 dígitos.

## API

| Método y ruta | Uso |
|---|---|
| `GET /reportes/categorias` | Motivos posibles |
| `GET /reportes/resultados` | Qué pasó en la llamada |
| `POST /numeros/consulta` | Cuántas personas reportaron un número y qué significa |
| `POST /reportes` | Reporta un número (cuenta y cabecera `X-Centinela`) |
| `GET /reportes/mios` | Reportes propios |
| `DELETE /reportes/{id}` | Retira un reporte propio |
| `POST /llamadas` con `{"numero": "..."}` | Empieza una conversación que tiene en cuenta la reputación del número |

## Cómo se probó

- `backend/tests/test_reportes.py`: cuentas nuevas en espera, avalancha de un día, estafa confirmada solo con pérdidas, publicidad aparte, disputa por llamadas legítimas, reportes viejos, respaldo por una conversación del mismo número, normalización de formatos, números inválidos, cuenta y cabecera obligatorias, un reporte por número, límite diario, consulta sin autores, número no guardado en claro (ni en un volcado de la base), retirar reportes, borrado al eliminar la cuenta, exportación, la señal que nunca decide sola y logs sin el número.
- En Chromium: reportar sin cuenta, tres personas que reportan el mismo número en formatos distintos, reporte repetido, retirar un reporte y una conversación con el número reportado que queda en moderado con la razón visible.

## Límites

- No hay verificación de que quien reporta recibió de verdad la llamada; la beta no puede leer el registro de llamadas del celular ([viabilidad.md](viabilidad.md)).
- Varias cuentas creadas por la misma persona pueden sumar reportes. El límite por IP en el registro, la espera de un día y el tope diario lo dificultan, pero no lo impiden.
- "Estafa confirmada" es una confirmación de la comunidad, no de una entidad. Una verificación oficial queda fuera del alcance de la beta.
- En Android, la consulta podría hacerse sola al entrar la llamada, con el filtrado de llamadas del sistema; en la beta web se escribe el número.
