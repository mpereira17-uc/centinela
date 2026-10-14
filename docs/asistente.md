# Asistente por voz (paso 5)

El asistente responde preguntas sobre la conversación que se está analizando. Se le puede hablar con el botón **Hablar** o escribirle, y responde en pantalla y en voz alta.

## Comandos

Son un conjunto cerrado, tomado de la sección 2.3 A de la especificación. No es un chat abierto: si la frase no coincide con ningún comando, el asistente dice qué puede hacer.

| Lo que dices | Qué responde |
|---|---|
| "¿Esta llamada parece una estafa?" | El nivel de riesgo de la conversación y qué hacer |
| "Explícame la alerta" | Las señales que encontró y que puede equivocarse |
| "Ayúdame a verificar la identidad de esta persona" | Cómo verificar por un canal independiente, y que la voz se puede clonar |
| "Analiza esta llamada" | Que no puede escuchar llamadas del celular y cómo darle la conversación |
| "Activa mi protección" | Que no vigila llamadas en segundo plano |
| "Quiero reportar este número" | Que esa función todavía no está disponible |
| "¿Qué puedes hacer?" | La lista de preguntas |

Las respuestas solo prometen lo que Centinela hace de verdad.

## La voz nunca ejecuta acciones sensibles

Si la frase pide desactivar, borrar, cambiar una clave o PIN, compartir, transferir o pagar, el asistente responde que eso no se hace por voz y marca `requiere_confirmacion`. Esas acciones se confirmarán en pantalla con PIN o passkey cuando exista el registro (paso 6). Esta regla se revisa antes que cualquier otro comando, para que una orden peligrosa nunca se confunda con una consulta.

## Cómo funciona la voz

- **Entrada:** el audio de la orden se transcribe con faster-whisper en el mismo equipo (ver [transcripcion.md](transcripcion.md)) y se descarta.
- **Salida:** la respuesta se lee con [Piper TTS](https://github.com/rhasspy/piper) en el mismo equipo. Si Piper no está configurado, la interfaz usa la voz del navegador. La casilla **Responder en voz alta** lo apaga.

Para usar Piper:

```bash
pip install -r requirements-ml.txt
python -m piper.download_voices es_MX-claude-high
export CENTINELA_VOZ_PIPER=$PWD/es_MX-claude-high.onnx   # En Windows: set CENTINELA_VOZ_PIPER=...
```

Cualquier voz en español de Piper sirve; la descarga necesita internet solo la primera vez.

## API

| Ruta | Entrada | Salida |
|---|---|---|
| `POST /asistente` | `{"texto": "...", "llamada_id": "..."}` | `intencion`, `respuesta`, `requiere_confirmacion` |
| `POST /asistente/voz` | Audio en `multipart/form-data` con `consentimiento=true` y `llamada_id` opcional | Lo anterior más `transcripcion` |
| `POST /voz` | `{"texto": "..."}` | Audio WAV, o 503 si Piper no está disponible |
| `GET /asistente/comandos` | — | Comandos con un ejemplo de cada uno |

## Criterios de aceptación

- [x] Los seis comandos de la especificación se reconocen, hablados o escritos.
- [x] La respuesta aparece en pantalla y se lee en voz alta, con Piper o con la voz del navegador.
- [x] Ninguna orden por voz desactiva protecciones, borra datos ni mueve dinero.
- [x] Sin conversación analizada, el asistente pide datos en vez de inventar un nivel.
- [x] Los errores (micrófono negado, transcripción no instalada, Piper ausente) tienen un mensaje claro y una alternativa.

## Verificación

Las pruebas están en `backend/tests/test_asistente.py`. La interfaz se probó en Chromium con un micrófono simulado. En el entorno de desarrollo no se pudieron descargar los modelos de Whisper ni de Piper, así que la transcripción real de órdenes y la voz de Piper deben probarse en el portátil del proyecto.
