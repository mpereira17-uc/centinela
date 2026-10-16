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

## Estilo Conversación (elegido el 15 de octubre de 2026)

pepe escogió, entre tres propuestas que se podían tocar en un celular de prueba (Conversación, Tablero y Escudo), el estilo **Conversación**, con colores más vivos. La idea es que Centinela se sienta como un chat que casi todos ya saben usar:

- Barra superior azul marino y fondo de chat con puntitos.
- El saludo de Centinela aparece como la primera burbuja del chat, y los accesos rápidos como respuestas en píldora.
- Las frases de quien llama van en burbujas blancas y las tuyas en burbujas azul claro.
- El resultado tiene una franja del color del nivel (verde, ámbar, naranja o rojo) con texto blanco.
- La alerta ocupa toda la pantalla con el color del nivel, un ícono grande con ondas y un botón blanco.
- Los niveles siguen distinguiéndose por forma del ícono y por texto, no solo por color.
- Tiene modo oscuro y respeta la opción de reducir el movimiento.

Solo cambió la hoja de estilos y el color de la barra del sistema (`theme-color`); el HTML, los identificadores y el JavaScript siguen iguales.

## Paleta Vigía (15 de octubre de 2026)

El verde jade vivo se veía fosforescente, sobre todo el rojo de las alertas y el modo oscuro. pepe pidió una paleta con personalidad propia y se compararon tres (Vigía, Bosque y Petróleo y coral; imágenes en `capturas/estilos/paleta-*.png` de la carpeta del proyecto). La elegida es **Vigía**, los colores de un centinela de noche:

- Azul marino (`#24426a` y `#1b2f4b`) en la barra, los botones y la burbuja propia.
- Ámbar de faro (`#e8a33d`) en el escudo, el foco del teclado y el pulso del micrófono.
- Niveles con tonos apagados para las alertas de pantalla completa: verde `#2e7d5b`, ámbar `#9a6c16`, naranja `#b85a28` y rojo vino `#a83636`. El texto blanco encima tiene un contraste de al menos 4,5 a 1 en los cuatro niveles.
- Modo oscuro casi negro azulado (`#0f1622`), superficies apagadas y los mismos niveles un poco más oscuros, para que no deslumbre de noche.

Todos los colores salen de variables al inicio de `estilos.css`; cambiar la paleta es cambiar ese bloque.

## Blanco y azul con el búho, y una interfaz para mayores (16 de octubre de 2026)

Reemplaza el estilo Conversación y la paleta Vigía. pepe pidió un logo propio, colores blanco con azul y una interfaz con menos texto para personas de la tercera edad, al estilo de las apps de transporte (DiDi, Uber) pero propia de Centinela. Está en la rama de la app Android; `main` no cambia hasta que pepe lo apruebe.

**Personaje.** El búho de Centinela es el logo y la figura que acompaña a la persona. Tiene cuatro caras según el riesgo, y la cara cambia sola con el nivel:

| Cara | Cuándo sale |
|---|---|
| Tranquilo (saluda con el ala) | Inicio y nivel bajo |
| Atento (escucha) | Mientras analiza o escucha por el altavoz, y números en revisión o de publicidad |
| Alerta (señala un aviso ámbar) | Riesgo moderado o alto, y números con reportes |
| Alarmado (levanta el ala para decir "detente") | Riesgo crítico y "probable estafa"; cejas de preocupación, no de enojo |

Los SVG están en `frontend/buho/` y salen de `node herramientas/buho.js`. El mismo búho es el ícono de la app instalable, el ícono adaptable de Android (con versión de una tinta para el ícono temático y la barra de notificaciones) y la imagen de la tarjeta que aparece encima de la llamada entrante.

**Colores.** Blanco de fondo y un azul propio, el azul Centinela (`#1D5BD6`, degradado de `#2B6BE4` a `#1446B8` para que el texto blanco siempre cumpla el contraste), con azul noche (`#0B2A5B`) para el texto. El ámbar y el rojo solo aparecen en los avisos de riesgo. Cada texto cumple contraste 4,5:1 sobre su fondo, y el modo oscuro es azul casi negro.

**Inicio.** Una pantalla con el búho que saluda, una barra grande "¿Quién te llama?" (como el "¿A dónde vas?" de las apps de transporte), seis botones grandes con ícono, nombre corto y una pista de pocas palabras (Estoy en una llamada, Revisar un mensaje, Escuchar mi llamada, Pregúntale, Me estafaron, Practicar), una lista "Más opciones" y un consejo corto que cambia cada vez. Abajo quedan solo tres pestañas: Inicio, Ayuda y Cuenta.

**Una pantalla por herramienta.** Cada herramienta se abre en su propia pantalla con un botón grande para volver; lo que no hace falta ver siempre (usar un audio, reportar un número, cómo evitamos reportes falsos) está plegado. Las pantallas viven en la misma página y se abren con su ancla (`#conversar`, `#quien-llama`, `#mensaje`, `#asistente`, `#denuncia`, `#como`), así el botón Atrás del celular vuelve al inicio y no se pierde la conversación. Los enlaces viejos siguen sirviendo: `/#numero-titulo` (el que abre la app Android desde la tarjeta de la llamada), `/#asistente`, `/#audio-titulo` y `/ayuda.html#me-estafaron` abren la pantalla que tiene esa parte. Ayuda usa el mismo patrón con cuatro botones: Verificar una entidad, Me estafaron, Palabra clave familiar y Contacto de confianza.

**Letra.** Base de 18 px, botones de al menos 54 px de alto y el botón "Aa" de la barra superior agranda todo un 18 % más.

## Aviso que pide una decisión (16 de octubre de 2026)

En **riesgo crítico**, el aviso de pantalla completa ya no se cierra con "Entendido". Pregunta "¿Qué vas a hacer?" y ofrece dos botones:

- **Cuelgo y verifico** (botón blanco, siempre disponible). El aviso pasa a azul, el búho se tranquiliza y dice "Bien hecho: cuelga y llama tú al número oficial de la entidad; si ya diste un código o una clave, llama a tu banco ahora", con el enlace al directorio de canales oficiales. En la llamada por Centinela cuelga de verdad, y en el modo acompañante deja de escuchar. En los dos casos aparece "¿Cómo terminó?".
- **Sigo, sé lo que hago** (botón de borde). Se habilita después de una pausa de 5 segundos, con la cuenta regresiva en el botón. Escape y deslizar hacia abajo solo valen como este botón y solo después de la pausa.

Los avisos moderados y altos siguen con "Entendido", para no volver pesada cada alerta. El respaldo está en la revisión de la FTC sobre mensajes de prevención: los avisos que piden una decisión funcionan mejor que los que se cierran con un toque, y hacer una pausa se asocia con menos fraude (ver el documento de ideas). Los botones del aviso no se bloquean mientras sigue el análisis de la conversación. Capturas 69 y 70.
