# Modo práctica

Pantalla `/practica.html` (acceso "Practicar" en las historias del inicio). Muestra 5 llamadas de mentira, con habla de distintas regiones, y la persona decide si cada una es estafa o normal. Al responder ve si acertó, qué delataba la estafa y la frase donde estaba la trampa, resaltada en la conversación.

## Para qué sirve

- **Entrenar sin riesgo**, sobre todo a personas mayores, antes de recibir una llamada real.
- **Probar la app en el piloto** con algo concreto que hacer, sin pedir datos.

## Cómo funciona

- `GET /practica/rondas?cantidad=5&semilla=` (límite: 30 por minuto por cliente). Toma llamadas de la [base de guiones](base-guiones.md) solo de las particiones `sintetica_prueba` y `regional`, que no entrenan el modelo, así practicar no cambia las cifras.
- Mitad estafa y mitad normal (con una de más al azar si la cantidad es impar), para que responder siempre "estafa" no gane.
- Cada ronda trae los turnos, la región, hasta 3 pistas (los motivos de las señales del [motor](motor-de-senales.md), primero lo que piden y luego la presión) y la frase clave.
- Las frases aparecen una por una, como en un chat; con movimiento reducido aparecen todas de una. El botón "Escuchar en voz alta" usa la voz del propio navegador (`speechSynthesis`, es-CO si existe), sin enviar nada.
- El mejor puntaje se guarda solo en el navegador (`localStorage`, `centinela-practica-mejor`). El servidor no guarda respuestas.

## Límites

- Las llamadas son guiones escritos, no grabaciones: sirven para aprender las señales, no para medir la precisión del modelo.
- Las pistas salen de las reglas del motor de señales; una llamada normal se explica con un consejo general, no con lo que "le falta".
