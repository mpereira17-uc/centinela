# Denunciar ante las autoridades

Cuando alguien intenta estafar a una persona, lo más útil después de colgar es denunciar. Centinela no envía nada a las autoridades por su cuenta. Arma un **resumen para la denuncia** y le muestra a la persona dónde presentarlo.

## Por qué no se envía solo

- **El número puede estar suplantado.** Lo que se ve en pantalla no prueba quién llamó; una denuncia automática podría acusar a un tercero.
- **Son datos personales.** Enviar a otra entidad la conversación, el número y quién denuncia requiere autorización expresa de la persona (Ley 1581 de 2012), y la denuncia la presenta la víctima con sus datos.
- **No hay una API pública** para que una aplicación radique denuncias en nombre de alguien. ADenunciar, de la Fiscalía y la Policía, es un formulario para personas y no tiene integración documentada para terceros.

## Qué hace Centinela

En la página principal, la tarjeta "Denunciar ante las autoridades":

1. La persona marca si perdió dinero o entregó datos.
2. "Preparar resumen" arma un texto con la fecha, el número que escribió (avisando que puede estar suplantado), las frases de la conversación con su nivel, las señales detectadas y una lista de datos que debe agregar: nombre, documento, a dónde envió dinero, montos, horas y capturas.
3. Puede copiarlo o descargarlo como `.txt`. Todo pasa en su celular: el resumen no se guarda ni se envía a ningún servidor.
4. Ve los canales que aplican:

| Canal | Cuándo | Se muestra |
|---|---|---|
| Línea 165 (GAULA) | Extorsión o amenazas | Si Centinela detectó amenaza |
| El banco, por su línea oficial | Pérdida de dinero: bloquear y pedir la reversión | Si marcó que perdió algo |
| [ADenunciar](https://adenunciar.policia.gov.co/) | Denuncia virtual por estafa o extorsión; permite adjuntar documentos | Siempre |
| [CAI Virtual](https://caivirtual.policia.gov.co/) | Policía Nacional, delitos informáticos y fraudes | Siempre |
| Línea 123 | Peligro inmediato | Siempre |

## Lo que viene de la regulación

La Resolución 8308 de 2026 de la CRC obliga a los operadores móviles a mostrar alertas de "llamada sospechosa" antes de contestar, a marcar las llamadas publicitarias de empresas registradas y a bloquear números irregulares, de forma gradual. No crea, por ahora, un canal público para que las personas o las aplicaciones reporten números. Si la CRC o su comité de lucha contra el fraude abren uno, los reportes con estado "probable estafa" ([reportes.md](reportes.md)) serían los candidatos a compartir, siempre con la autorización de quienes reportaron.

Fuentes: [Policía Nacional, ADenunciar](https://www.policia.gov.co/noticia/sistema-denuncia-virtual-adenunciar-crece), [Semana, alertas de llamada sospechosa](https://www.semana.com/tecnologia/articulo/antes-de-responder-una-llamada-su-celular-le-advertira-si-podria-tratarse-de-una-estafa-asi-funcionara-la-alerta-en-colombia/202608/), [Portafolio, Resolución 8308 de 2026](https://www.portafolio.co/tecnologia/adios-al-spam-telefonico-colombia-pone-en-marcha-nuevas-reglas-para-frenar-el-fraude-503996). Consultadas el 15 de octubre de 2026.
