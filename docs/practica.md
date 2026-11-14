# Modo práctica

Pantalla `/practica.html` (botón "Practicar" del inicio). Muestra 5 llamadas de mentira, con habla de distintas regiones, y la persona decide si cada una es estafa o normal. Al responder ve si acertó, qué delataba la estafa y la frase donde estaba la trampa, resaltada en la conversación.

Las llamadas se ordenan en **4 niveles por táctica**, con racha de días e insignias, y arriba sale **la estafa de la semana** con un botón para practicarla. La idea viene de ShieldUp! (arXiv 2503.12341), que entrena por tácticas de manipulación, y de los estudios de advertencia previa (forewarning) que resume la FTC: conocer la modalidad antes de recibir la llamada ayuda a reconocerla.

## Para qué sirve

- **Entrenar sin riesgo**, sobre todo a personas mayores, antes de recibir una llamada real.
- **Probar la app en el piloto** con algo concreto que hacer, sin pedir datos.

## Niveles, racha e insignias

| Nivel | Táctica | Estafas | Llamadas normales parecidas |
|---|---|---|---|
| 1. Premios y paquetes | Te ofrecen un premio o te retienen un paquete, y piden pagar primero | `premio_falso`, `envio_falso` | `comercio`, `domicilio` |
| 2. Familiar en apuros | Dicen ser de tu familia, con número nuevo o en una emergencia, y piden plata ya | `familiar_falso` | `familia` |
| 3. Urgencia con tu banco o tu operador | Te asustan con un fraude o una falla y piden un código o instalar una app | `suplanta_banco`, `soporte_falso` | `banco`, `banco_real`, `servicios` |
| 4. Autoridad y amenazas | Hablan como cobranza, juzgado o grupo armado, y te amenazan si no pagas | `extorsion`, `suplanta_entidad` | `salud`, `colegio`, `trabajo` |

- Cada nivel mezcla sus estafas con llamadas normales del mismo tema (la tienda de verdad, el familiar de verdad, el banco de verdad), para que no baste con sospechar de todo lo que suene al tema. Una prueba verifica que cada llamada de práctica cae en un solo nivel y que cada nivel alcanza para 10 rondas mitad y mitad.
- Todos los niveles están abiertos; se recomiendan en orden. Con **4 de 5** se gana la insignia del nivel (el búho dentro del círculo). Quien ya la tiene ve "Siguiente nivel"; quien no, "Intentar otra vez".
- La **racha** cuenta los días seguidos con al menos una práctica, con la fecha del celular. Si pasó más de un día sin practicar, vuelve a cero. "Mezcla de todo" también cuenta para la racha, pero no da insignias.
- Insignias, mejor puntaje por nivel y racha se guardan solo en el navegador (`localStorage`, `centinela-practica-progreso`). Si ese dato está dañado, la pantalla arranca de cero sin fallar.

## La estafa de la semana

- `GET /practica/semana` devuelve una modalidad que circula en Colombia, explicada en tres líneas (qué dicen, qué buscan, qué hacer), y el nivel donde se practica. Cambia cada lunes en hora Colombia y recorre las 8 modalidades antes de repetir: falso asesor del banco, familiar con número nuevo, paquete retenido, falsa cobranza o embargo, falso técnico del operador, premio que nunca jugaste, emergencia de un familiar y extorsión por teléfono.
- Sale en el inicio, encima de "Más opciones", y arriba de la pantalla de práctica. "Practicar esta" abre `/practica.html?nivel=…` y empieza ese nivel de una.
- Es una tarjeta dentro de la app, no una notificación: así no se pide otro permiso ni se manda nada al celular sin que la persona abra Centinela.

## Cómo funciona

- `GET /practica/niveles` da los 4 niveles en orden con su táctica y cuántas llamadas tiene cada uno.
- `GET /practica/rondas?cantidad=5&semilla=&nivel=` (`nivel` es opcional: `premios`, `familiar`, `urgencia` o `autoridad`; sin él es la mezcla de todo; límite: 90 por minuto por cliente, porque en la sustentación varios celulares del mismo wifi comparten dirección). Toma llamadas de la [base de guiones](base-guiones.md) solo de las particiones `sintetica_prueba` y `regional`, que no entrenan el modelo, así practicar no cambia las cifras.
- Mitad estafa y mitad normal (con una de más al azar si la cantidad es impar), para que responder siempre "estafa" no gane.
- Cada ronda trae los turnos, la región, hasta 3 pistas (los motivos de las señales del [motor](motor-de-senales.md), primero lo que piden y luego la presión) y la frase clave.
- Las frases aparecen una por una, como en un chat; con movimiento reducido aparecen todas de una. El botón "Escuchar en voz alta" usa la voz del propio navegador (`speechSynthesis`, es-CO si existe), sin enviar nada.
- El mejor puntaje de la mezcla se guarda solo en el navegador (`localStorage`, `centinela-practica-mejor`). El servidor no guarda respuestas.

## Límites

- Las llamadas son guiones escritos, no grabaciones: sirven para aprender las señales, no para medir la precisión del modelo.
- Las pistas salen de las reglas del motor de señales; una llamada normal se explica con un consejo general, no con lo que "le falta".
