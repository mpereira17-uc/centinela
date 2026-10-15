# Clasificador entrenado

Paso 11 de la [hoja de ruta](hoja-de-ruta.md). La [evaluación del paso 10](evaluacion.md) mostró que las reglas fallan con las estafas que evitan las palabras típicas: 50 % de detección en los guiones reservados. El clasificador aprende de ejemplos para reconocer esas variaciones.

## Modelo

- **Características:** palabras, pares de palabras y trozos de 3 a 5 letras de cada palabra, sin tildes ni mayúsculas. Los trozos de letras ayudan con conjugaciones ("consigne", "consígnelo") y errores de transcripción.
- **Pesos:** TF-IDF con frecuencia sublineal, como `TfidfVectorizer(sublinear_tf=True)` de scikit-learn.
- **Clasificador:** regresión logística con clases balanceadas.
- **Unidad:** cada frase de quien llama. Da la probabilidad de que sea una solicitud de riesgo según la [guía de anotación](guia-anotacion.md).

## Datos de entrenamiento

Solo datos de desarrollo:

| Fuente | Frases de riesgo | Frases sin riesgo |
|---|---|---|
| [datos/entrenamiento/frases.json](../datos/entrenamiento/frases.json), escritas para entrenar | 80 | 80 |
| Turnos de quien llama de los 24 guiones de desarrollo | 12 | 48 |

En los guiones de riesgo se toma como positiva la frase anotada en `turno_riesgo`; las frases posteriores ("sí, rápido") se descartan porque son ambiguas. Una prueba verifica que ninguna frase de los guiones reservados entre al entrenamiento.

## Umbral

Se elige con validación cruzada de 5 partes sobre los datos de entrenamiento: el umbral que más frases de riesgo detecta sin pasar de 3 % de falsas alertas por frase. Quedó en **0,61**, con 71 % de detección y 1,6 % de falsas alertas por frase fuera de muestra. Por llamada la detección es mayor, porque basta con que una frase supere el umbral.

## Estrategia híbrida

La híbrida es la acumulación de reglas más el clasificador: si alguna de las frases recientes supera el umbral, suma la señal `patron_aprendido`, de tipo solicitud. Por las reglas de niveles eso lleva a **alto**, o a **crítico** si además hay presión. El clasificador nunca quita señales que hayan encontrado las reglas.

El aviso dice "lo que te piden se parece a estafas conocidas" y la explicación aclara que es un modelo estadístico que puede equivocarse. No se muestran porcentajes, como en el resto de la app.

## Resultados en los guiones reservados

Modo texto, 6 llamadas de riesgo y 6 legítimas que el modelo nunca vio ([informe](../datos/resultados/evaluacion-texto-reservada.md)):

| Estrategia | Detección | Falsas alertas | Aviso (mediana) | Alertas anticipadas |
|---|---|---|---|---|
| Reglas por fragmento | 3/6 | 1/6 | 6,4 s | 0 |
| Reglas con acumulación | 3/6 | 1/6 | 6,4 s | 0 |
| Clasificador solo | 6/6 | 0/6 | 5,6 s | 2 |
| **Híbrida** | **6/6** | 1/6 | 5,6 s | 2 |

- El clasificador detecta las tres estafas que las reglas no ven: el préstamo para "mandarlo a la cuenta de un amigo" (r14), el "número de verificación de WhatsApp" (r15) y el "léame el mensaje" (r18).
- La falsa alerta de la híbrida (l13, el banco que pide **no** compartir un código) viene de las reglas, no del clasificador.
- Las dos alertas anticipadas llegan un turno antes de la solicitud: en r14 con "cambié de número, guárdeme este" y en r15 con "le va a llegar un mensaje con un número de verificación". Son frases típicas de esas estafas, pero también podría decirlas alguien legítimo; hay que vigilarlas.
- Con 6 llamadas por grupo el intervalo de confianza de 6/6 va de 61 % a 100 %: el resultado es prometedor, no definitivo.

En los guiones de desarrollo la híbrida detecta 12/12, pero esa cifra es optimista porque el modelo se entrenó con esos mismos turnos.

## Por qué la híbrida es la estrategia visible

`CENTINELA_ESTRATEGIA_VISIBLE` pasa de `acumulacion` a `hibrida`: duplica la detección en los guiones reservados con las mismas falsas alertas que la acumulación, y conserva las razones concretas de las reglas ("te piden un código o una clave"). El clasificador solo tuvo menos falsas alertas, pero sus avisos no pueden explicar qué se pidió. Para volver a las reglas basta con `CENTINELA_ESTRATEGIA_VISIBLE=acumulacion`. Las tres estrategias se siguen calculando y guardando en cada frase.

## Cómo se aplica sin scikit-learn

El modelo se guarda en [backend/app/modelo_clasificador.json](../backend/app/modelo_clasificador.json) (unas 4.000 características): vocabulario, pesos IDF, coeficientes, intercepto y umbral. `backend/app/clasificador.py` repite el cálculo de scikit-learn con Python puro, así que el servidor no necesita scikit-learn ni abre archivos pickle, que pueden ejecutar código al cargarse (modelo de amenazas, A19). Una prueba compara las probabilidades con las de scikit-learn hasta la novena cifra decimal (se omite si scikit-learn no está instalado, como en la integración continua).

Si el archivo no existe, la híbrida no se activa y la interfaz vuelve a la acumulación de reglas.

## Reentrenar

```bash
pip install -r requirements-ml.txt
cd backend
python -m evaluacion.entrenar                          # escribe app/modelo_clasificador.json
python -m evaluacion.evaluar --particion reservada     # compara con las reglas
```

Si se agregan frases o guiones, deben ir a desarrollo. Si se ajusta algo mirando los errores de la partición reservada, esa partición deja de servir para medir y hay que escribir guiones reservados nuevos.

## Límites

- 160 frases escritas y 24 guiones son pocos datos. El modelo aprende el estilo de quien escribió los ejemplos; puede fallar con guiones reales distintos.
- Trabaja frase por frase: no entiende el hilo de la conversación más allá de la ventana de la acumulación.
- BETO u otros modelos de lenguaje quedaron fuera: con tan pocos datos no hay cómo compararlos de forma justa, y harían más pesada la beta.
