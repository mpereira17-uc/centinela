# Hoja de ruta

Cada paso llega como un commit directo a `main`, con criterios de aceptación, pruebas y documentación, y solo se sube si todas las pruebas pasan. Los pasos 1 y 2 llegaron como PR; desde el paso 3 se suben directo, a pedido de pepe. El alcance sale de [viabilidad.md](viabilidad.md).

| Paso | Qué entrega | Criterios de aceptación | Estado |
|---|---|---|---|
| 0 | Esqueleto: backend FastAPI y dos estrategias de alerta | El backend arranca y pasan las pruebas | Hecho |
| 1 | Viabilidad técnica, modelo de amenazas y esta hoja de ruta | Cada función de la especificación tiene decisión; cada amenaza tiene mitigación y paso | Hecho |
| 2 | Motor de señales v1 | Catálogo de señales de la sección 2.1 con explicación; niveles bajo, moderado, alto y crítico con reglas verificables y sin porcentajes; mensaje de alerta accionable por nivel; límites de tamaño de entrada; logs sin texto de la conversación | Hecho |
| 3 | Interfaz web accesible | Pantalla para analizar una conversación por fragmentos; alerta con ícono, texto y color; lectura correcta con lector de pantalla; texto insertado sin HTML | Hecho |
| 4 | Transcripción de audio | Subir o grabar audio con consentimiento visible; transcripción local con faster-whisper; el audio no se guarda | Hecho |
| 5 | Asistente por voz | Comandos cerrados ("¿parece estafa?", "explícame la alerta"); respuesta hablada con Piper y en pantalla; la voz nunca ejecuta acciones sensibles | Hecho |
| 6 | Registro seguro | Passkeys con PIN alternativo (Argon2); límite de intentos; sesiones revocables; consentimientos separados | Hecho |
| 7 | Historial y datos personales | Historial de alertas en SQLite; retención limitada; exportar y borrar todos los datos | Hecho |
| 8 | Reporte de números | Reportes seudónimos con límite por cuenta; la reputación pesa como una señal más | Pendiente |
| 9 | Llamada simulada por WebRTC | Dos navegadores en llamada con análisis en vivo y un solo aviso visible | Pendiente |
| 10 | Conjunto simulado y evaluación | Guiones legítimos y de riesgo con voces de Piper; script que mide detección, falsas alertas, error de transcripción y tiempo de aviso | Pendiente |
| 11 | Clasificador entrenado | TF-IDF y regresión logística comparados con las reglas en llamadas reservadas | Pendiente |

## Trabajo futuro (fuera de la beta)

Se abordan solo si la evaluación muestra que son viables, precisos y seguros:

- App nativa Android con `CallScreeningService` para identificar números antes de contestar.
- Autenticación vocal opcional como factor adicional, nunca único.
- Detección de voz clonada, presentada siempre con sus limitaciones.
- Análisis de SMS y enlaces.
