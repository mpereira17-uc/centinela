# Base de guiones

Todos los guiones de Centinela viven en una sola base con el mismo formato, se consultan por una API y alimentan el clasificador y la evaluación. Hoy son 264 llamadas: 48 escritas a mano y 216 generadas desde plantillas, de 9 regiones de Colombia.

## Por qué no se usa una base externa

No existe una base abierta y gratuita de guiones de estafas telefónicas en español de Colombia. Las denuncias de la Policía y la SIC no tienen API abierta, y las bases de empresas como Truecaller son de pago y tratan de números, no de lo que se dice en la llamada. Por eso la base se arma aquí, con un formato fijo que después puede recibir las llamadas del piloto en Bogotá.

## Formato

Cada guion sigue [datos/guiones/esquema.json](../datos/guiones/esquema.json) (JSON Schema). Lo valida `evaluacion/guiones.py` al cargar.

| Campo | Qué dice |
|---|---|
| `id` | Único en toda la base |
| `etiqueta` | `riesgo` o `legitima` |
| `categoria` | Tipo de estafa (`suplanta_banco`, `extorsion`...) o de llamada legítima (`familia`, `banco_real`...) |
| `particion` | Para qué sirve (tabla de abajo) |
| `region` | Región de los modismos, si aplica |
| `fuente` | `escrito` (a mano), `plantilla` (generado) o `piloto` (transcrito de una llamada del piloto, con consentimiento) |
| `plantilla` | Plantilla de origen, si es generado |
| `turno_riesgo` | Turno de quien llama con la solicitud de riesgo; vacío en las legítimas |
| `turnos` | Lista de `[hablante, texto]` |

| Partición | Archivo | Llamadas | Uso |
|---|---|---|---|
| `desarrollo` | [guiones.json](../datos/guiones/guiones.json) | 24 | Entrena y ajusta |
| `reservada` | guiones.json | 12 | Solo para el informe final |
| `regional` | [guiones-regionales.json](../datos/guiones/guiones-regionales.json) | 12 | Mide modismos; no entrena |
| `sintetica_desarrollo` | [guiones-sinteticos.json](../datos/guiones/guiones-sinteticos.json) | 126 | Entrena |
| `sintetica_prueba` | guiones-sinteticos.json | 90 | Mide; no entrena |

## Guiones generados desde plantillas

[datos/guiones/plantillas.json](../datos/guiones/plantillas.json) tiene 24 plantillas (12 de riesgo y 12 legítimas) con huecos como `{saludo}`, `{trato}`, `{pida}`, `{codigo}`, `{monto}` o `{afan}`. Cada región trae sus propias variantes: "sumercé" y "regáleme los dígitos" en Bogotá, "mijo" y "páseme el codiguito" en Antioquia, "mirá, pasame" en el Valle, "compadre" y "un melón" en los Llanos. `python -m evaluacion.generar_guiones` llena cada plantilla una vez por región. La elección de variantes es fija para cada pareja plantilla-región, así que el archivo no cambia entre corridas y una prueba verifica que esté al día.

Las legítimas usan los mismos modismos y también hablan de plata, de afán o de bancos ("ya le pasé la plata del mercado", "hágale ya mismo que el jefe quiere empezar", "su tarjeta nueva está lista en la oficina"), para que el modelo no aprenda que una región o un tema son señal de estafa.

Para agregar guiones basta con agregar una plantilla, o variantes a una región, y volver a generar. Cada plantilla nueva multiplica por nueve.

**Plantillas de prueba aparte.** 7 plantillas de riesgo y 7 legítimas son de entrenamiento; las otras 5 y 5 son de prueba y nunca entrenan. Así la partición `sintetica_prueba` mide si el modelo reconoce una forma de estafa que no vio, no solo otra región de la misma frase.

## API

Solo lectura, sin cuenta, con límite de 60 consultas por minuto:

- `GET /guiones?etiqueta=riesgo&region=bogota&categoria=extorsion&particion=&fuente=&desde=0&limite=50`: guiones filtrados y paginados (máximo 200 por página), con `total`.
- `GET /guiones/resumen`: cuántos hay por partición, etiqueta, categoría, región y fuente, y qué particiones entrenan.
- `GET /guiones/esquema`: el formato de arriba.

Lee los mismos archivos que el entrenamiento y la evaluación, así que lo que devuelve es exactamente lo que ve el modelo. Se puede probar en http://localhost:8000/docs.

## Cambios en el clasificador

- **Entrena también con las plantillas de entrenamiento:** 63 frases de riesgo y 297 sin riesgo más.
- **Validación cruzada por grupos.** Las nueve versiones regionales de una plantilla caen siempre en la misma parte. Si unas entrenaran y otras validaran, la validación saldría casi perfecta y el umbral, muy bajo (0,54 en lugar de 0,63).
- **El umbral se mide sobre las frases escritas a mano.** Las sintéticas entrenan, pero no cuentan al medir, porque cada frase dudosa aparecería nueve veces. Quedó en 0,63, con 76 % de detección y 2 % de falsas alertas por frase fuera de muestra (antes 0,68, con 64 % y 2 %). Después se ajustó a 0,61 al sumar respuestas cortas legítimas ([clasificador](clasificador.md)).

## Resultados

| Partición | Híbrida antes | Híbrida después | Clasificador antes | Clasificador después |
|---|---|---|---|---|
| Desarrollo (12 + 12) | 12/12 y 1/12 falsas | igual | 12/12 y 0/12 | igual |
| Reservada (6 + 6) | 6/6 y 1/6 | igual | 6/6 y 0/6 | 6/6 y 1/6 |
| Regional (6 + 6) | 6/6 y 0/6 | igual | 5/6 y 0/6 | 6/6 y 0/6 |
| Sintética de prueba (45 + 45) | 37/45 y 0/45 | 45/45 y 0/45 | 37/45 y 0/45 | 45/45 y 0/45 |

- **La primera medición sobre las plantillas de prueba sí fue a ciegas,** y encontró un hueco real: la extorsión que dice "tiene que colaborarnos con doscientos mil o le va a ir mal a su familia" no se detectaba (0 de 9 regiones). Se agregaron al [diccionario de modismos](modismos.md) "colaborarnos con" + un monto como solicitud de dinero y "le va a ir mal" como amenaza. La cifra de después ya no es a ciegas.
- **El clasificador solo** tiene una falsa alerta nueva en la reservada, l13, el banco que pide no compartir un código. Es la misma que ya tenía la híbrida por las reglas, así que lo que ve el usuario no cambia.
- Los informes completos están en [datos/resultados/](../datos/resultados/), incluido [el de la partición sintética](../datos/resultados/evaluacion-texto-sintetica_prueba.md).

## Límites

- **Guiones sintéticos no son llamadas reales.** Los escribió el mismo equipo que escribió las reglas, y salen de pocas plantillas. Sirven para cubrir regiones y variantes, pero un 100 % en ellos no dice cuánto detectará Centinela en la calle.
- **La cifra que vale** saldrá del piloto en Bogotá: llamadas reales o simuladas con personas, transcritas con su consentimiento, sin nombres ni apodos, y agregadas a la base con `fuente: "piloto"` en una partición que no entrene.
