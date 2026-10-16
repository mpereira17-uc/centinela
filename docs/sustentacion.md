# Sustentación: que los jurados instalen Centinela y la prueben en vivo

La idea es que cada jurado escanee un código QR, instale Centinela en su celular y la pruebe en ese momento. Para eso hay cuatro piezas:

| Pieza | Qué hace | Dónde |
|---|---|---|
| App instalable | Centinela se instala desde el navegador con su ícono, en Android o iPhone, sin pasar por la Play Store | `manifest.webmanifest`, `sw.js`, `instalar.html` |
| Modo acompañante | Escucha por el altavoz una llamada telefónica normal y avisa en vivo | `acompanante.html` |
| Llamada entre redes | La llamada de prueba conecta aunque cada celular esté en una red distinta (datos o Wi‑Fi) | `GET /webrtc/ice` |
| Arranque | Un comando enciende el servidor en el portátil con una dirección pública HTTPS y muestra el QR | `sustentacion.py` |

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

## Lista de ensayo (hazla con dos días de anticipación)

- [ ] `python sustentacion.py` muestra la dirección y el QR.
- [ ] Un celular Android con datos móviles (sin Wi‑Fi) abre el QR e instala la app.
- [ ] Compartir un mensaje desde WhatsApp y desde Mensajes abre Centinela con el texto y lo revisa.
- [ ] Un iPhone, si consigues uno, la agrega a inicio desde Safari.
- [ ] Modo acompañante con una llamada real en altavoz: la alerta aparece antes de terminar la frase del código. Si la transcripción falla, acerca el dispositivo al altavoz o sube el volumen de la llamada.
- [ ] Llamada por Centinela entre un celular con datos y otro en Wi‑Fi: se oyen y aparece el aviso.
- [ ] Grabar en video los pasos 1 a 4 del guion: es el **plan B** si falla internet en el salón.
- [ ] Llevar el cargador del portátil y, por si acaso, activar el punto de acceso del celular como red de respaldo.

## Privacidad

- El audio del modo acompañante se transcribe en el portátil y se descarta; no se guarda. La pantalla pide confirmar que las personas de la llamada saben que se escucha.
- El service worker guarda solo la interfaz (HTML, CSS, JS e íconos), nunca respuestas de la API.
- Las claves del TURN viven en `backend/.env`, que no se versiona, y nunca se escriben en los registros.

## Límites para decirlos tal cual

- La app instalable funciona mientras el portátil y el túnel estén encendidos. Es una demostración, no un servicio público.
- El modo acompañante depende de que el altavoz se oiga claro: con ruido fuerte la transcripción empeora y el aviso puede tardar más.
- El túnel gratuito de Cloudflare (`trycloudflare.com`) no tiene garantía de disponibilidad. Por eso existe el video del plan B.
