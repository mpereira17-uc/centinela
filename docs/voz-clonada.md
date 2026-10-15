# Señal experimental de voz clonada

Con unos segundos de audio de redes sociales se puede imitar la voz de una persona. Los detectores gratuitos de voz sintética todavía fallan mucho, sobre todo con audio de teléfono, acentos colombianos y voces nuevas que no vieron al entrenarse. Por eso Centinela trata esta señal como **experimental** y con tres reglas fijas:

1. **Solo puede subir el nivel, nunca bajarlo.** Las dos partes agregan señales, y el cálculo de niveles nunca baja al agregar una señal. Hay una prueba que lo comprueba turno a turno en los 264 guiones de la [base](base-guiones.md).
2. **Nunca dice que una voz es auténtica.** Si no hay señal, no significa nada; ningún texto de la app afirma que la voz sea real.
3. **La defensa principal no es técnica:** la [palabra clave familiar](palabra-clave.md) y colgar para llamar al número de siempre.

## Parte 1: por contexto (siempre activa)

`voz_dudosa`, de tipo presión. Aparece cuando en la conversación hay alguien que dice ser de la familia o un conocido (`finge_conocido`) o cuenta una emergencia familiar (`emergencia_familiar`), **y además** pide plata, un código o datos de la tarjeta. Es el guion típico de la voz clonada ("abuela, soy yo, tuve un accidente, consígneme"). Como es presión, junto con la solicitud lleva el nivel a crítico, lo que activa el botón del [contacto de confianza](contacto-confianza.md) y el consejo de la palabra clave.

No cambió ninguna cifra de la evaluación (aciertos y falsas alarmas iguales en desarrollo, reservada, regional y sintética de prueba): esas llamadas ya llegaban a alto por la solicitud. Lo que cambia es que suben a crítico y el aviso explica por qué la voz no es prueba de nada.

## Parte 2: acústica (apagada por defecto)

`app/voz_clonada.py` tiene un `DetectorAcustico` que se activa solo si se instala un modelo ONNX y se indica su ruta:

```bash
pip install -r requirements-ml.txt   # trae onnxruntime (lo usa Piper)
export CENTINELA_MODELO_VOZ=/ruta/al/modelo.onnx
export CENTINELA_UMBRAL_VOZ=0.9    # opcional; alto a propósito
```

- El modelo recibe audio mono a 16 kHz (`float32`, forma `[1, n]`, máximo 30 segundos) y su última salida debe ser la probabilidad de voz sintética.
- Solo se usa con el audio que la persona sube en una llamada, en memoria, y se descarta igual que en la transcripción.
- Si el puntaje supera el umbral se agrega `voz_sintetica`, de tipo contexto: sola llega a precaución y no dispara el aviso; suma con lo demás. Una vez marcada, la llamada no se desmarca.
- Si el modelo no está, falla o el puntaje es bajo, no se agrega nada.

No se incluye un modelo porque ninguno gratuito se ha validado con llamadas colombianas. Para el documento, el camino es probar uno entrenado con ASVspoof 2019/2021 o In-the-Wild contra grabaciones del piloto (con consentimiento) y voces clonadas propias, y reportar sus falsas alarmas antes de activarlo.
