# Modismos y variantes regionales

La beta se prueba con personas de Bogotá, pero quien llama a estafar puede hablar como en cualquier región. Por eso Centinela reconoce frases y modismos comunes en todo el país: "léame los numeritos" es lo mismo que "dígame el código", y "mándeme cien lucas" es una solicitud de dinero.

## Cómo funciona

1. **Diccionario de modismos** ([backend/app/modismos.py](../backend/app/modismos.py)). Antes de buscar señales, el texto (en minúsculas y sin tildes) se lleva a una forma común. Solo se reemplazan expresiones; no se borra nada. Grupos:
   - El código por mensaje: numeritos, codiguito, clavecita, mensajito, token.
   - Plata: lucas, luquitas, barras, palos, melones, platica.
   - Pedir dinero: mándeme, pásame, eche, colabóreme con, regáleme, me presta... seguido de plata, pesos, lucas; y Bre-B.
   - Bajar una aplicación: bájese, descargue... una aplicación.
   - Afán: hágale ya, a la de ya, de afán, volando, ahí mismo.
   - Amenaza: le caemos, lo tenemos ubicado, sabemos dónde vive, pagar la vacuna, boleteo.
   - Secreto: no le vaya a contar, no me vaya a colgar, esto queda entre los dos.
   - Conocido falso: adivine quién le habla, este es mi número nuevo, se me dañó el celular. Es una señal nueva de contexto, `finge_conocido`.
2. **Excepción informativa.** "Ya le pasé por Nequi la plata" o "ya te consigné" cuentan algo que ya pasó; no piden una transferencia y no la marcan.
3. **Frases de entrenamiento regionales** ([datos/entrenamiento/frases-regionales.json](../datos/entrenamiento/frases-regionales.json)): 36 de riesgo y 36 legítimas de la Costa Caribe, Antioquia, Bogotá, el Valle, Santander, Nariño, los Llanos, Tolima y Huila y el Eje Cafetero. Las legítimas usan los mismos modismos ("quiubo, parce", "sumercé", "mi llave", "achichay") para que el modelo no aprenda que hablar con modismos de una región es señal de estafa.

## Resultados

Partición `regional` ([guiones-regionales.json](../datos/guiones/guiones-regionales.json)): 12 llamadas simuladas, 6 de riesgo y 6 legítimas, una por región en cada grupo. Nunca se usan para entrenar.

| Estrategia | Antes: detección | Antes: falsas alertas | Después: detección | Después: falsas alertas |
|---|---|---|---|---|
| Reglas (por fragmento) | 5/6 | 1/6 | 6/6 | 0/6 |
| Clasificador | 5/6 | 0/6 | 5/6 | 0/6 |
| Híbrida (la visible) | 6/6 | 1/6 | 6/6 | 0/6 |

Antes, las reglas no reconocían "léame los numeritos del mensajito" (g01) y alertaban en falso cuando un hijo le contaba a su mamá "ya le pasé por Nequi la plata" (g12). En las particiones de desarrollo y reservada los resultados no cambiaron. Informe completo: [evaluacion-texto-regional.md](../datos/resultados/evaluacion-texto-regional.md).

**Cuidado al leer esta tabla.** Los guiones regionales se escribieron antes del diccionario, pero el diccionario se ajustó viendo dónde fallaban. La mejora es real para esas frases, pero no es una medición a ciegas. La cifra que vale para el informe saldrá de llamadas nuevas del piloto en Bogotá, anotadas con la [guía de anotación](guia-anotacion.md).

## Límites

- **El acento de la voz** no lo resuelve el diccionario: depende de que el transcriptor escriba bien lo que oye. Hablas costeñas que aspiran la "s" ("lo número de atrá") o muy rápidas pueden transcribirse mal. Para medirlo hacen falta grabaciones de personas de varias regiones leyendo los guiones, con su consentimiento ([evaluacion.md](evaluacion.md), modo audio).
- **Apodos y nombres propios** no se guardan en la base: no ayudan a detectar la estafa (la señal está en lo que se pide) y serían datos personales.
- Los modismos cambian rápido. El diccionario es un archivo de reglas fácil de ampliar con lo que aparezca en el piloto.
