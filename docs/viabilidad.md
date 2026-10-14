# Análisis de viabilidad técnica

Este documento revisa cada función de la [especificación](especificacion.md) frente a tres preguntas: si se puede construir hoy, qué permisos o integraciones exige y de qué servicios externos depende. La conclusión define el alcance de la beta de tesis, que debe costar cero pesos en efectivo y apoyarse en llamadas simuladas, como fija el anteproyecto.

Fecha de revisión: 14 de octubre de 2026. Las capacidades de Android e iOS cambian con cada versión, así que las afirmaciones sobre plataformas deben volver a verificarse antes de construir una app nativa.

## 1. La restricción principal: el audio de una llamada celular

Una app ordinaria **no puede escuchar el audio de una llamada celular en curso**, ni en Android ni en iOS.

- **Android.** Capturar la voz de una llamada (`AudioSource.VOICE_CALL`) exige el permiso `CAPTURE_AUDIO_OUTPUT`, reservado a apps del sistema. Mientras hay una llamada activa, el sistema tampoco garantiza que otra app reciba audio del micrófono. Google Play prohíbe además usar la API de accesibilidad para grabar llamadas. Lo que sí está permitido es `CallScreeningService` (Android 10 en adelante), que entrega el número entrante para identificarlo, avisar o bloquearlo antes de contestar, pero no da acceso al audio.
- **iOS.** No existe ninguna API pública de acceso al audio de llamadas. CallKit permite una extensión de identificación y bloqueo a partir de listas de números, y las versiones recientes añaden consultas de identificación en vivo con protección de privacidad; ninguna de las dos entrega audio.
- **Los detectores de estafas que ya existen** dentro de la llamada, como el de los teléfonos Pixel, funcionan porque los integra el fabricante del sistema operativo. Una app de terceros no tiene ese acceso.

**Consecuencia para Centinela:** el análisis de la conversación se hace sobre audio que el usuario aporta de forma voluntaria y visible, nunca interceptando la llamada. Para la tesis, eso significa:

1. **Llamada simulada por WebRTC** entre dos navegadores, en la que ambos participantes saben que se analiza. Es una conversación real entre dos personas, pero no pasa por la red celular.
2. **Reproducción controlada** de llamadas grabadas o sintetizadas, para el conjunto de prueba.
3. **Transcripción aportada por el usuario**, pegada o dictada después de la llamada, para pedir una segunda opinión.

## 2. Viabilidad por función

Leyenda: **Beta** = se construye en la beta de tesis. **Después** = viable, pero queda fuera del tiempo o del costo de la beta. **Investigar** = no se implementa hasta comprobar su precisión, privacidad y seguridad.

| Función (sección de la especificación) | ¿Se puede hoy? | Permisos o integraciones | Servicios externos | Decisión |
|---|---|---|---|---|
| Análisis de la conversación en una llamada simulada (2.1, 2.2) | Sí | Micrófono del navegador, con consentimiento | Ninguno: Whisper corre en local | **Beta** |
| Análisis de una transcripción aportada por el usuario (6) | Sí | Ninguno | Ninguno | **Beta** |
| Niveles de riesgo bajo, moderado, alto y crítico con razones (2.2, 7) | Sí, con reglas verificables y luego un clasificador | Ninguno | Ninguno | **Beta** |
| Alertas breves y accionables (2.1, 9) | Sí | Ninguno | Ninguno | **Beta** |
| Asistente por voz con respuestas habladas (2.3 A) | Sí, con un conjunto cerrado de comandos | Micrófono | Ninguno: Whisper y Piper en local | **Beta** |
| Confirmación de acciones sensibles fuera de la voz (2.3 D) | Sí | Ninguno | Ninguno | **Beta** |
| Registro con passkeys y PIN alternativo (3) | Sí, con WebAuthn en el navegador | Autenticador del dispositivo | Ninguno | **Beta** |
| Consultar, exportar y borrar datos; revocar sesiones (3, 5) | Sí | Ninguno | Ninguno | **Beta** |
| Reporte seudónimo de números y reputación como señal (7, 10) | Sí, a escala de prueba | Ninguno | Ninguno | **Beta** (sin moderación a gran escala) |
| Identificación de números antes de contestar (6) | Sí, en una app nativa | `CallScreeningService` en Android; CallKit en iOS | Base de reputación propia | **Después** |
| App nativa publicada en tiendas (6) | Sí | Cuenta de desarrollador | Play Store cuesta 25 USD; App Store, 99 USD al año | **Después** |
| Análisis de SMS y enlaces (6, 7) | Parcialmente | Permisos de SMS muy restringidos por Google Play | Listas de enlaces maliciosos | **Después** |
| Autenticación vocal (2.3 B) | Técnicamente sí (modelos libres de verificación de hablante) | Micrófono | Ninguno | **Investigar**: es dato biométrico sensible (Ley 1581) y es vulnerable a voces clonadas |
| Detección de voz clonada (2.3 C) | Solo como investigación | Micrófono | Ninguno | **Investigar**: los detectores fallan con técnicas nuevas y no hay garantía |
| Escuchar llamadas celulares reales | No para apps de terceros | Permisos de sistema | — | **Descartado** |

## 3. Alcance de la beta de tesis

La beta es una **aplicación web progresiva** (se abre en el navegador del celular o del computador y se puede instalar en la pantalla de inicio) con un backend FastAPI que corre en el portátil del estudiante. Se elige web y no app nativa porque no cuesta nada, sirve igual en Android y en iOS para las pruebas, y la función central, el análisis de la conversación, no depende de permisos nativos.

Incluye:

1. Motor de señales con niveles de riesgo explicables y las dos estrategias del anteproyecto (por fragmento y acumulación de indicios).
2. Interfaz accesible para analizar una conversación y mostrar alertas que no dependen solo del color.
3. Transcripción local con faster-whisper; el audio no se guarda por defecto.
4. Asistente por voz con comandos cerrados y respuesta con Piper TTS.
5. Registro con passkeys o PIN, sesiones revocables y consentimientos separados.
6. Historial de alertas con retención limitada, y exportación y borrado de datos.
7. Reporte seudónimo de números, tratado como señal y nunca como prueba.
8. Llamada simulada por WebRTC con análisis en vivo.
9. Conjunto de llamadas simuladas y script de evaluación con las métricas del anteproyecto: detección, falsas alertas, error de transcripción y tiempo de aviso.

No incluye: biometría vocal, detección de clonación, app nativa, análisis de SMS ni acceso a llamadas celulares. Quedan documentados como trabajo futuro con sus condiciones.

## 4. Costos

Todo el software es libre y corre en local. El desembolso en efectivo de la beta es **$0**. El presupuesto del anteproyecto valora como aporte en especie el portátil, las horas del estudiante y las del director. Si se necesita entrenar más rápido, Google Colab gratuito es suficiente para un clasificador TF-IDF y para probar BETO.

## 5. Riesgos de viabilidad

| Riesgo | Efecto | Respuesta |
|---|---|---|
| Whisper en CPU es lento | El aviso llega tarde | Usar modelos `base` o `small` con int8 y medir la demora, que es una métrica de la tesis |
| Pocas llamadas de entrenamiento | El clasificador generaliza mal | Mantener las reglas como referencia y separar las familias de guion antes de entrenar |
| Voces de Piper poco naturales | Las pruebas no se parecen a una llamada real | Combinar voces sintéticas con grabaciones de voluntarios que consientan |
| Navegadores que limitan el micrófono fuera de HTTPS | La llamada simulada no funciona en el celular | Usar `localhost` o un certificado local para las pruebas |
