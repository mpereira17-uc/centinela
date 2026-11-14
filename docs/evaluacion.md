# Evaluación

Paso 10 de la [hoja de ruta](hoja-de-ruta.md). Mide qué tan bien avisa Centinela con llamadas simuladas cuya respuesta correcta se conoce de antemano.

## Datos

36 guiones en [datos/guiones/guiones.json](../datos/guiones/guiones.json), escritos y etiquetados con la [guía de anotación](guia-anotacion.md):

| | Riesgo | Legítimas |
|---|---|---|
| Desarrollo | 12 | 12 |
| Reservada | 6 | 6 |

Los de riesgo cubren suplantación de banco y entidades, familiar falso, soporte técnico, premios, inversión, envíos, empleo y extorsión, con dos guiones que evitan las palabras típicas. Los legítimos incluyen casos difíciles: el banco que habla de seguridad sin pedir nada, un código que se pide **no** compartir, un premio sin costo y una urgencia familiar sin dinero.

## Qué se mide

| Métrica | Definición |
|---|---|
| Detección | Llamadas de riesgo en las que aparece el aviso |
| Falsas alertas | Llamadas legítimas en las que aparece el aviso |
| Precisión | De todos los avisos, cuántos fueron en llamadas de riesgo |
| Tiempo de aviso | Desde que empieza el turno con la solicitud de riesgo hasta que termina el turno que dispara el aviso (más la transcripción, en modo audio) |
| F1 | Media armónica de precisión y detección |
| Demora | Desde que **termina** la primera petición riesgosa hasta el aviso, con el mismo reloj del audio. Puede ser negativa si avisa antes. Se resume con mediana y percentil 95, solo de las llamadas detectadas; las no detectadas se listan aparte |
| Avisos tardíos | Demora mayor que la admisible, fijada en **5 s antes de probar** (`--demora-admisible`) |
| Alertas anticipadas | Avisos antes del turno de riesgo anotado |
| WER | Tasa de error de palabra de la transcripción frente al texto del guion, total y por voz |

Cada tasa va con su intervalo de confianza del 95 % (Wilson), porque con 6 a 18 llamadas por grupo una diferencia de un caso mueve mucho el porcentaje. Solo se analizan los turnos de quien llama, como en la [llamada simulada](llamada.md).

### Comparación llamada a llamada

Las dos estrategias reciben los mismos fragmentos, así que se comparan sobre las mismas llamadas: el informe lista en cuáles avisa solo una y la diferencia en detección y falsas alertas, en puntos porcentuales, con un intervalo del 95 % por remuestreo. Se remuestrean **familias completas** (una plantilla con sus nueve regiones cuenta como una), porque las variantes regionales comparten la forma del engaño; contarlas como independientes daría una certeza falsa. Si el intervalo toca el cero, la diferencia no es concluyente.

### Familias de indicios graduales

La pregunta del proyecto solo se puede responder con llamadas donde ningún turno basta por sí solo. Por eso [plantillas.json](../datos/guiones/plantillas.json) incluye, solo para prueba (nunca para entrenar):

- **6 engaños graduales** (`gradual_*`): el falso banco que manda al cajero, la falsa DIAN que cobra en un corresponsal, el sobrino accidentado, el premio de la transportadora, la inversión con cupos y el falso policía. Ninguno pide códigos ni transferencias; reparten entidad, amenaza, prisa y aislamiento en varios turnos.
- **6 llamadas legítimas difíciles** (`dificil_*`): el banco que de verdad bloquea la tarjeta, el recordatorio real de la DIAN, el jefe con prisa y reserva, el papá varado, el regalo del operador y la clínica que avisa un accidente. Las tres primeras juntan tres indicios sueltos sin que haya engaño.

Con ellas aparece la disyuntiva que estudia el proyecto (partición sintética de prueba, modo texto):

| Estrategia | Detección | Falsas alertas | F1 |
|---|---|---|---|
| por_fragmento | 44/99 (44 %) | 0/99 (0 %) | 62 % |
| acumulacion | 98/99 (99 %) | 27/99 (27 %) | 88 % |

Acumular indicios detecta los engaños graduales que la decisión por fragmento deja pasar (+54,5 pp, IC 95 %: +27,3 a +81,8, por familias), a cambio de alertar en las llamadas legítimas que juntan varios indicios sueltos. Ese costo es el que hay que examinar antes de concluir que una estrategia es mejor en general.

## Cómo correrla

Modo texto (no necesita modelos, tarda menos de un segundo):

```bash
cd backend
python -m evaluacion.evaluar --particion desarrollo
```

Modo audio (necesita `pip install -r requirements-ml.txt` y voces de Piper en español):

```bash
cd backend
python -m evaluacion.generar_audio --voz-llamante voces/VOZ_1.onnx --voz-usuario voces/VOZ_2.onnx
python -m evaluacion.evaluar --modo audio --particion desarrollo --nombre voz1
```

Para revisar si la transcripción falla más con algún tipo de voz (modelo de amenazas, A14), se genera el audio con varias voces de quien llama, en carpetas distintas (`--salida` y `--audio`), y se compara la WER de cada informe.

Cada corrida escribe `datos/resultados/evaluacion-<modo>-<partición>[-<nombre>].json` y `.md`.

## Resultados en modo texto

Reglas del [motor de señales](motor-de-senales.md) con el nivel de alerta por defecto (`alto`), antes del clasificador. Informes completos: [desarrollo](../datos/resultados/evaluacion-texto-desarrollo.md), [reservada](../datos/resultados/evaluacion-texto-reservada.md), [todas](../datos/resultados/evaluacion-texto-todas.md), [regional](../datos/resultados/evaluacion-texto-regional.md) (ver [modismos.md](modismos.md)), [sintética de prueba](../datos/resultados/evaluacion-texto-sintetica_prueba.md) (ver [base-guiones.md](base-guiones.md)).

| Partición | Estrategia | Detección | Falsas alertas | Aviso (mediana) |
|---|---|---|---|---|
| Desarrollo | Por fragmento | 10/12 (83 %) | 0/12 | 6,4 s |
| Desarrollo | Acumulación | 10/12 (83 %) | 1/12 | 6,4 s |
| Reservada | Por fragmento | 3/6 (50 %) | 1/6 | 6,4 s |
| Reservada | Acumulación | 3/6 (50 %) | 1/6 | 6,4 s |

Lo que muestran:

- **Las reglas fallan con las estafas que evitan las palabras típicas.** No detectan "léame los seis números que le llegaron" (r09), "léame el mensaje" (r18), un código de WhatsApp pedido como "número de verificación" (r15), un préstamo para "mandarlo a la cuenta de un amigo" (r14) ni una extorsión que dice "si no nos manda" (r06).
- **La caída en la partición reservada (83 % a 50 %)** es la señal esperada de que las reglas se escribieron mirando ejemplos parecidos a los de desarrollo. Es el problema que ataca el clasificador del paso 11.
- **Falsas alertas:** l13 (el banco menciona un código pero pide no compartirlo) alerta con ambas estrategias; l06 (el banco habla de seguridad y bloqueo) alerta solo con acumulación, porque suma tres señales de contexto a lo largo de la llamada.
- **Tiempo de aviso:** cuando detecta, avisa al terminar el mismo turno de la solicitud, unos 6 a 8 segundos después de que empieza, según la duración estimada del turno.

## Comparación con el clasificador (paso 11)

Con el [clasificador](clasificador.md) entrenado, el mismo script compara cuatro estrategias. En la partición reservada:

| Estrategia | Detección | Falsas alertas |
|---|---|---|
| Reglas por fragmento | 3/6 | 1/6 |
| Reglas con acumulación | 3/6 | 1/6 |
| Clasificador solo | 6/6 | 0/6 |
| Híbrida (reglas + clasificador) | 6/6 | 1/6 |

Los detalles y la decisión de usar la híbrida como estrategia visible están en [clasificador.md](clasificador.md).

## Resultados en modo audio

Corrida del 14 de noviembre de 2026 en el portátil del proyecto, CPU, Whisper `base`, voz de quien llama `es_MX-claude-high` y de quien contesta `es_ES-davefx-medium`, las 372 llamadas ([informe](../datos/resultados/evaluacion-audio-todas-claude-high.md)). La síntesis tardó 5 minutos y la evaluación 15.

| Estrategia | Detección texto | Detección audio | Falsas alertas audio | F1 audio |
|---|---|---|---|---|
| por_fragmento | 86 % | 35 % | 1 % | 52 % |
| acumulacion | 93 % | 72 % | 4 % | 81 % |
| clasificador | 100 % | 83 % | 1 % | 90 % |
| hibrida | 100 % | 96 % | 5 % | 96 % |

WER: **12,5 %**. La demora mediana es de 0,8 a 0,9 s después de la petición riesgosa.

**Hallazgo:** los errores de transcripción caen justo en las palabras que buscan las reglas: "Nequi" sale "NECY", "Daviplata" sale "David Plata", "consignes" sale "consigues" y "dígitos" sale "tígitos". Por eso las reglas pierden mucho más que el clasificador, que no depende de una palabra exacta. Con audio la acumulación sigue superando a la decisión por fragmento (+36,0 pp en detección, IC 95 %: +18,0 a +53,6, por familias), y combinar reglas y clasificador (híbrida) es lo más robusto. Siguiente paso: darle a Whisper el vocabulario colombiano (bancos, billeteras, entidades) como `initial_prompt` o `hotwords`, validarlo solo con la partición de desarrollo y repetir la corrida, para no ajustar con los datos de prueba.

## Límites

- 36 guiones es una muestra pequeña: los intervalos de confianza son anchos y sirven para comparar estrategias, no como cifra definitiva.
- Los guiones los escribió el mismo equipo que escribió las reglas. La partición reservada reduce, pero no elimina, ese sesgo; lo ideal es sumar guiones escritos por otras personas.
- En modo texto los tiempos son estimados (2,5 palabras por segundo y 0,6 s entre turnos).

## Fuera del laboratorio

Las llamadas de prueba del piloto preguntan al colgar cómo terminó. `GET /desenlaces/resumen` da la tabla de aciertos y falsas alarmas con esas respuestas ([cómo-termino.md](como-termino.md)).
