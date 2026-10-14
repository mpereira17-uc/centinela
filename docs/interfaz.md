# Interfaz web (paso 3)

La interfaz se abre en el navegador del celular o del computador en `http://127.0.0.1:8000/` cuando el backend está encendido. Sirve para escribir una conversación frase por frase y ver el nivel de riesgo a medida que avanza. No escucha llamadas: solo analiza el texto que se escribe.

![Ejemplo de estafa en el celular](capturas/movil-estafa.png)

## Qué tiene

- **Agregar una frase** con quién la dijo (la persona que llama o yo). Enter envía y Shift+Enter hace un salto de línea.
- **Nivel de riesgo actual**, que cambia con cada frase.
- **Aviso principal**, que aparece una sola vez por conversación cuando el nivel llega al umbral de alerta. Toma el foco para que el lector de pantalla lo lea de inmediato.
- **Conversación** con el nivel después de cada frase y un "¿Por qué?" que lista las señales.
- **Ejemplos** de una llamada de estafa y una legítima, marcados como guiones inventados.
- **¿Cómo decide Centinela?**, con los cuatro niveles y la lista de señales que trae `GET /senales`.

## Accesibilidad

- Cada nivel se distingue por **forma del ícono, texto y color**: círculo con ✓ (bajo), cuadrado con ! (moderado), triángulo con ! (alto) y octágono con ✕ (crítico).
- El aviso usa `role="alert"` y el nivel usa `aria-live="polite"`.
- Formulario con etiquetas, mensajes de error anunciados y botones de al menos 44 px de alto.
- Enlace para saltar al contenido, foco visible, modo oscuro automático y sin animaciones si el sistema pide reducir movimiento.
- Diseño de una columna que funciona desde 360 px de ancho.

## Seguridad

- Todo texto del usuario se inserta con `textContent`, nunca como HTML.
- Política CSP estricta sin scripts ni estilos en línea, y cabeceras `X-Content-Type-Options`, `Referrer-Policy` y `Permissions-Policy`.
- La ayuda del formulario pide no escribir claves ni números de tarjeta reales.

## Manejo de errores

| Situación | Qué ve el usuario |
|---|---|
| Frase vacía | "Escribe una frase antes de analizar." |
| Frase de más de 2000 caracteres | El campo no deja escribir más; si llega al servidor, aviso de frase demasiado larga |
| Servidor apagado | "No pudimos conectar con Centinela. Revisa que el servidor esté encendido." |
| El servidor se reinició y perdió la conversación | Se crea una conversación nueva y se reintenta la frase una vez |
| Demasiadas frases en una conversación | "Esta conversación llegó al máximo de frases. Empieza una nueva." |

## Criterios de aceptación

- [x] Se puede analizar una conversación por fragmentos y ver el nivel tras cada uno.
- [x] La alerta muestra ícono, texto y color, y no se repite en la misma conversación.
- [x] El aviso se anuncia al lector de pantalla y recibe el foco.
- [x] El texto del usuario nunca se interpreta como HTML (probado con `<img onerror>`).
- [x] Funciona en celular y en escritorio, en modo claro y oscuro, sin errores en la consola.

Las pruebas automáticas están en `backend/tests/test_interfaz.py`. La revisión en navegador se hizo con Chromium a 390 px y 1280 px.
