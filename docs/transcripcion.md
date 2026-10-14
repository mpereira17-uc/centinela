# Transcripción de audio (paso 4)

Centinela puede analizar un audio además del texto escrito. El audio se convierte en texto con [faster-whisper](https://github.com/SYSTRAN/faster-whisper) **en el mismo equipo donde corre el backend**, y cada segmento transcrito pasa por el motor de señales como si fuera una frase escrita.

## Cómo usarlo

1. Instala las dependencias de voz una sola vez: `pip install -r requirements-ml.txt`.
2. Enciende el backend y abre la interfaz.
3. En **Analizar un audio**, marca la casilla de consentimiento.
4. Pulsa **Grabar con el micrófono** y luego **Detener y analizar**, o usa **Subir un archivo de audio**.

La primera vez, faster-whisper descarga el modelo (`base`, unos 145 MB) y necesita internet. Después funciona sin conexión. El tamaño se cambia con `CENTINELA_MODELO_WHISPER` (`tiny` es más rápido y menos preciso; `small` es más preciso y más lento).

## API

`POST /llamadas/{id}/audio`, en `multipart/form-data`:

| Campo | Obligatorio | Descripción |
|---|---|---|
| `audio` | Sí | Archivo de audio de hasta 10 MB |
| `consentimiento` | Sí | Debe ser `true` |
| `hablante` | No | Etiqueta para los fragmentos |

Responde con un resultado por segmento (mismo formato que `POST /llamadas/{id}/fragmentos`) y `mostrar_aviso` si alguno disparó el aviso. Los tiempos de los segmentos continúan después de lo que ya tenía la conversación.

## Privacidad

- El audio se lee en memoria, se transcribe y se descarta. **No se escribe en disco** ni se envía a ningún servicio externo.
- No se puede grabar ni subir sin marcar el consentimiento, y el servidor rechaza la solicitud sin él.
- Los registros del servidor solo guardan cuántos segmentos salieron, nunca el texto ni el audio.
- El navegador pide permiso para el micrófono; la política `Permissions-Policy` solo lo permite a la propia página.

## Manejo de errores

| Situación | Respuesta | Qué ve el usuario |
|---|---|---|
| Sin consentimiento | 400 | Le pide marcar la casilla |
| Archivo que no es audio | 415 | "El archivo no es de audio" |
| Audio vacío | 400 | "El audio está vacío" |
| Más de 10 MB | 413 | "El audio supera los 10 MB" |
| Audio que no se puede decodificar | 422 | Formatos aceptados |
| faster-whisper sin instalar | 503 | El comando para instalarlo |
| El modelo no se pudo descargar | 503 | Que la primera vez necesita internet |
| Navegador sin micrófono o permiso negado | — | Sugiere subir un archivo |

## Criterios de aceptación

- [x] Se puede grabar o subir audio, siempre con consentimiento visible.
- [x] La transcripción corre en local con faster-whisper, en CPU con int8.
- [x] El audio no se guarda en disco y se procesa fuera del bucle principal del servidor.
- [x] Cada segmento se analiza con las dos estrategias y respeta el aviso único por conversación.
- [x] Todos los errores de la tabla tienen prueba o se verificaron en el navegador.

## Limitaciones y verificación

Las pruebas automáticas (`backend/tests/test_audio.py`) reemplazan el modelo por segmentos fijos, para que corran rápido y sin descargar nada. La grabación con micrófono y la subida de archivos se probaron en Chromium con un micrófono simulado. En el entorno donde se desarrolló este paso no había acceso a la descarga del modelo, así que **la transcripción real con faster-whisper debe probarse en el portátil del proyecto** antes de usarla en las mediciones del paso 10.
