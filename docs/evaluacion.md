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
| Alertas anticipadas | Avisos antes del turno de riesgo anotado |
| WER | Tasa de error de palabra de la transcripción frente al texto del guion, total y por voz |

Cada tasa va con su intervalo de confianza del 95 % (Wilson), porque con 6 a 18 llamadas por grupo una diferencia de un caso mueve mucho el porcentaje. Solo se analizan los turnos de quien llama, como en la [llamada simulada](llamada.md).

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

**Pendiente.** Este entorno no puede descargar los modelos de Whisper ni las voces de Piper, así que el modo audio se probó solo con voz y transcripción simuladas (`backend/tests/test_evaluacion.py`). Hay que correrlo en el portátil del proyecto con los comandos de arriba y agregar aquí la WER y los tiempos reales.

## Límites

- 36 guiones es una muestra pequeña: los intervalos de confianza son anchos y sirven para comparar estrategias, no como cifra definitiva.
- Los guiones los escribió el mismo equipo que escribió las reglas. La partición reservada reduce, pero no elimina, ese sesgo; lo ideal es sumar guiones escritos por otras personas.
- En modo texto los tiempos son estimados (2,5 palabras por segundo y 0,6 s entre turnos).
