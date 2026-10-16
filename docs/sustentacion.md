# Sustentación: que los jurados instalen Centinela y la prueben en vivo

La idea es que cada jurado escanee un código QR, instale Centinela en su celular y la pruebe en ese momento. Para eso hay cinco piezas:

| Pieza | Qué hace | Dónde |
|---|---|---|
| App instalable | Centinela se instala desde el navegador con su ícono, en Android o iPhone, sin pasar por la Play Store | `manifest.webmanifest`, `sw.js`, `instalar.html` |
| Modo acompañante | Escucha por el altavoz una llamada telefónica normal y avisa en vivo | `acompanante.html` |
| Llamada entre redes | La llamada de prueba conecta aunque cada celular esté en una red distinta (datos o Wi‑Fi) | `GET /webrtc/ice` |
| Arranque | Un comando enciende el servidor en el portátil con una dirección pública HTTPS, muestra el QR y deja la voz cargada | `sustentacion.py` |
| Revisión previa | Cada celular revisa, con su propia red, que la llamada conecte entre redes, que la voz esté lista y que el micrófono oiga | `revisar.html` |

## Por qué así y no desde la Play Store

- Las cuentas personales nuevas de Play Console deben pasar 14 días de prueba cerrada con al menos 12 testers antes de publicar, y después viene la revisión. La app instalable desde el navegador no depende de eso.
- Si además se quiere mostrar la descarga desde Google Play, la **prueba interna** de Play Console acepta hasta 100 correos y no tiene revisión larga. Requiere los correos de Gmail de los jurados antes del día.

## Lo que Centinela puede y no puede escuchar

Ni Android ni iPhone dejan que una app oiga el audio de una llamada telefónica normal, aunque sea el teléfono predeterminado: ese audio solo lo reciben las apps del sistema. Por eso hay dos caminos:

- **Llamada por Centinela** (internet, como WhatsApp): Centinela analiza directamente la voz de quien llama.
- **Llamada telefónica normal en altavoz con el modo acompañante**: otro dispositivo con Centinela escucha por su micrófono. El celular de la llamada no sirve para esto, porque el teléfono ocupa su micrófono mientras dura la llamada.

## Preparación (una sola vez, en el portátil)

1. Instalar Python 3.11 o superior y las dependencias, incluidas las de voz:
   ```bash
   pip install -r requirements-ml.txt
   ```
   La primera transcripción descarga el modelo de Whisper. Hazla antes del día, con internet.
2. Instalar **cloudflared**, gratuito, que da la dirección pública con HTTPS:
   - Windows: `winget install --id Cloudflare.cloudflared`
   - macOS: `brew install cloudflared`
3. Configurar el **TURN** para que la llamada por Centinela conecte entre redes distintas. Con el de Cloudflare, que tiene uso gratuito: en su panel, en la sección de Realtime, crea una llave de TURN. Te da un identificador de la llave y un token de API. Luego crea `backend/.env` (no se sube al repositorio):
   ```
   CENTINELA_CLOUDFLARE_TURN_LLAVE=el_identificador_de_la_llave
   CENTINELA_CLOUDFLARE_TURN_TOKEN=el_token_de_api
   ```
   Centinela pide credenciales temporales de un día y las renueva solo. Cualquier otro TURN sirve con `CENTINELA_TURN_URL`, `CENTINELA_TURN_USUARIO` y `CENTINELA_TURN_CLAVE`, y un STUN con `CENTINELA_STUN_URL`. Sin nada configurado, la llamada sigue funcionando en la misma red, como en la beta. El modo acompañante y el resto de la app no necesitan TURN.

## El día de la sustentación

```bash
python sustentacion.py
```

Muestra la dirección (`https://….trycloudflare.com`) y el QR en la terminal, y abre la página de instalación. Esa página también muestra el QR para proyectarlo. Deja la ventana abierta y el portátil conectado a la corriente.

Antes de mostrar el QR, la terminal dice si la llamada por Centinela tiene TURN (si no, avisa que solo conecta en la misma red) y empieza a cargar el modelo de voz, para que la primera frase de la demo no espere. Si no configuraste un STUN, usa el público y gratuito de Cloudflare (`stun.cloudflare.com`), que ayuda a conectar entre algunas redes aunque falte el TURN.

Luego abre `/revisar.html` en **cada celular** que vas a usar, con la red que va a usar (datos o Wi‑Fi). Revisa la conexión con el portátil, si la voz ya cargó y cuánto tarda cada frase, si el TURN responde desde esa red (abre una conexión de prueba de verdad) y, con un botón, si el micrófono oye. Si todo sale en verde, las llamadas están listas.

La dirección cambia cada vez que se arranca: arráncalo una sola vez, al llegar al salón.

### Números de ejemplo para la app Android

Con `python sustentacion.py --demo` se cargan tres números ya reportados por cuentas de ejemplo, para que la tarjeta sobre la llamada se vea sin esperar reportes reales:

| Número | Aviso en la tarjeta |
|---|---|
| 300 000 0001 | Probable estafa (franja ámbar) |
| 300 000 0002 | Posible estafa (franja ámbar) |
| 601 000 0003 | Publicidad o call center |

Con 300 000 0001 o 300 000 0002, si el celular tiene el timbre normal, Centinela además dice en voz alta "Cuidado: probable estafa…" mientras timbra y vibra con tres toques cortos; en modo vibración solo vibra y en silencio o No molestar no hace nada. Se apaga en *Ajustes > Decir el aviso en voz alta*. Si en *Ayuda > Contacto de confianza* hay alguien guardado, la notificación de esos números trae el botón *Llamar a …*.

Para mostrar el [bloqueo opcional](bloqueo.md), enciende *Ajustes > Rechazar llamadas de estafas confirmadas* y simula una llamada desde 300 000 0001: no timbra y llega la notificación de llamada rechazada. Desde 300 000 0002 sí timbra, porque no es una estafa confirmada. Apágalo al terminar.

Se guardan solo en la base del portátil. Para borrarlos: desde `backend/`, `python -m app.demo --quitar`. Dilo tal cual a los jurados: son datos de ejemplo; los reportes reales que hagan ellos en la demo cuentan aparte.

## Guion de la demostración

1. **Instalar.** Proyecta `/instalar.html`. Los jurados escanean el QR y tocan *Instalar Centinela* (en iPhone: Compartir → Agregar a inicio).
2. **Revisar un mensaje.** Envíale a un jurado por WhatsApp un SMS sospechoso inventado. El jurado lo mantiene presionado, busca *Compartir* y elige Centinela: el aviso aparece sin copiar ni pegar. Si en su celular no aparece *Compartir*, que lo copie y lo pegue en *Revisar un mensaje*.
3. **Modo acompañante.** Llama desde tu celular al número de un jurado, por la red normal. El jurado pone el altavoz y otro jurado abre *Acompañante* en su celular y toca *Empezar a escuchar*. Haz el papel de estafador ("le hablamos del banco… dícteme el código que le llegó") y la alerta aparece en el segundo celular.
4. **Llamada por Centinela.** Desde *Llamada*, crea una llamada, dicta el código al jurado y que se una con *Recibo la llamada*. Ve el aviso directo en su pantalla, sin altavoz.
5. **Práctica.** Un jurado toca "Practicar esta" en la estafa de la semana del inicio y hace las 5 llamadas de ese nivel. Con 4 de 5 gana la insignia y se ve la racha; si no, sale "Intentar otra vez".
6. **Cierre.** Proyecta el *Tablero de la comunidad* (desde la página de instalar) mientras los jurados reportan desde su celular el número que les llamó en la demo: el total sube solo. Muestra *¿Cómo terminó?* y explica los límites de la sección anterior.

## Si algo falla en plena demo

| Qué pasa | Qué hace Centinela sola | Qué haces tú |
|---|---|---|
| Se corta la conexión con el portátil (el túnel, la señal) durante la llamada por Centinela | La voz sigue, porque va directo entre los celulares. Cada celular vuelve a entrar solo con la llave de la llamada; el lugar se guarda 45 segundos. Un mensaje cada 20 segundos evita que el túnel cierre la conexión por silencio | Nada. Si pasan los 45 segundos, crea otra llamada |
| Se corta el audio (un celular cambia de Wi‑Fi a datos) | Quien llama reinicia la conexión del audio, con credenciales nuevas del TURN, hasta 3 veces | Si no vuelve: sigan en **modo texto** (quien llama escribe sus frases y el aviso sale igual) |
| La llamada por Centinela no conecta entre redes (no hay TURN o no responde) | `/revisar.html` lo dice antes de empezar | Conecta los dos celulares al mismo Wi‑Fi o al punto de acceso de tu celular: en la misma red no hace falta TURN |
| El modo acompañante no oye el altavoz | La barra debajo de "Escuchando" muestra cuánto oye; con voz se pone blanca y dice "Oigo la llamada" | Acerca el celular al altavoz o sube el volumen de la llamada |
| Cada frase tarda más de 3 segundos en el portátil | `/revisar.html` lo dice | Agrega `CENTINELA_WHISPER_HAZ=1` en `backend/.env` y arranca de nuevo: tarda más o menos la mitad, con un poco menos de precisión |
| La voz no está instalada en el portátil | `/revisar.html` y la terminal lo dicen | Usa la llamada por Centinela en modo texto, o el video |
| Se cae internet en el salón | — | El video del plan B |

### Por qué los avisos por voz llegan más rápido

Antes, el celular enviaba el audio en trozos fijos de 6 segundos: una frase como "dícteme el código que le llegó" podía quedar partida en dos, y el aviso esperaba a que se completaran los 6 segundos. Ahora el celular mide el volumen y cierra cada trozo cuando quien habla hace una pausa de 0,7 segundos (o a los 8 segundos si no para), así que cada trozo lleva frases completas y se analiza apenas termina la frase. Los silencios no se envían. Si el navegador no deja medir el volumen, vuelve solo a trozos fijos. En la prueba con un audio de frases y pausas, el trozo salió 0,7 segundos después de cada frase; el tiempo de transcripción en el portátil se suma a eso.

## Lista de ensayo (hazla con dos días de anticipación)

- [ ] `python sustentacion.py` muestra la dirección y el QR, y dice que la llamada tiene TURN.
- [ ] `/revisar.html` en verde en cada celular, con la red de cada uno.
- [ ] Un celular Android con datos móviles (sin Wi‑Fi) abre el QR e instala la app.
- [ ] Compartir un mensaje desde WhatsApp y desde Mensajes abre Centinela con el texto y lo revisa.
- [ ] Un iPhone, si consigues uno, la agrega a inicio desde Safari.
- [ ] Modo acompañante con una llamada real en altavoz: la alerta aparece antes de terminar la frase del código. Si la transcripción falla, acerca el dispositivo al altavoz o sube el volumen de la llamada.
- [ ] Llamada por Centinela entre un celular con datos y otro en Wi‑Fi: se oyen y aparece el aviso.
- [ ] En plena llamada por Centinela, apaga los datos del celular que llama 5 segundos y vuelve a encenderlos: la llamada debe seguir sola.
- [ ] Deja el modo acompañante escuchando 2 minutos sin tocar el celular: la pantalla no se apaga (en la app de Android y en Chrome).
- [ ] Grabar en video los pasos 1 a 4 del guion: es el **plan B** si falla internet en el salón.
- [ ] Llevar el cargador del portátil y, por si acaso, activar el punto de acceso del celular como red de respaldo.

## Privacidad

- El audio del modo acompañante se transcribe en el portátil y se descarta; no se guarda. La pantalla pide confirmar que las personas de la llamada saben que se escucha.
- El service worker guarda solo la interfaz (HTML, CSS, JS e íconos), nunca respuestas de la API.
- Las claves del TURN viven en `backend/.env`, que no se versiona, y nunca se escriben en los registros.

## Lo que solo se comprueba con celulares reales

Aquí se probó con dos navegadores en un mismo equipo y audio simulado: la llamada conecta, sobrevive a un corte de la conexión con el servidor y a un reinicio del audio, y la escucha corta los trozos en las pausas (también con la voz que llega por la llamada). Falta comprobar en celulares:

- Que Whisper entienda bien la voz que sale por un altavoz y cuánto tarda en tu portátil (`/revisar.html` lo muestra después de la primera frase).
- Que el TURN conecte entre operadores colombianos con datos móviles.
- Que la app de Android mantenga la pantalla encendida mientras escucha (pide `FLAG_KEEP_SCREEN_ON` a la app; en Chrome lo hace el navegador).
- En iPhone, si Safari no deja medir el volumen, la escucha vuelve a trozos fijos de 6 segundos: funciona, pero el aviso tarda un poco más.

## Límites para decirlos tal cual

- La app instalable funciona mientras el portátil y el túnel estén encendidos. Es una demostración, no un servicio público.
- El modo acompañante depende de que el altavoz se oiga claro: con ruido fuerte la transcripción empeora y el aviso puede tardar más.
- El túnel gratuito de Cloudflare (`trycloudflare.com`) no tiene garantía de disponibilidad. Por eso existe el video del plan B.
