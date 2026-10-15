# Palabra clave familiar

La clonación de voz con inteligencia artificial puede imitar a un hijo, una mamá o un nieto con pocos segundos de audio, y ningún detector gratuito es confiable. La defensa que sí funciona no es técnica: una palabra secreta acordada en familia.

## En la app

- **Pantalla Ayuda > Palabra clave familiar:** explica cómo escogerla (en persona, que no se pueda adivinar, solo para emergencias) y tiene una casilla "Ya acordé una palabra clave con mi familia".
- **Centinela nunca pide ni guarda la palabra.** Solo recuerda en el navegador (`localStorage`) que la familia tiene una.
- **En el aviso:** cuando una llamada trae `finge_conocido` ("adivine quién le habla", "mi número nuevo") o la nueva señal `emergencia_familiar` (accidente, detención, robo, clínica), el aviso agrega:
  - con palabra acordada: "Pregúntale la palabra clave que acordaron en familia. Si no la sabe, cuelga, aunque la voz suene igual."
  - sin palabra: "Cuelga y llama tú al número de siempre de esa persona. La voz se puede imitar con inteligencia artificial."

## La señal `emergencia_familiar`

Es de contexto: sola llega a moderado y no dispara el aviso. Sirve para sumar con lo que se pida después ("consígneme ya") y para dar el consejo de la palabra clave. Se comprobó que no cambia ninguna cifra de la evaluación en desarrollo, reservada, regional ni sintética de prueba.
