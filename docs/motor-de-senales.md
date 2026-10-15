# Motor de señales (paso 2)

El motor revisa el **contenido** de lo que se dice en la llamada y decide un nivel de riesgo. No analiza la voz, el acento, el género ni la edad de quien habla. El código está en `backend/app/senales.py`.

## Señales

| Señal | Tipo | Qué detecta |
|---|---|---|
| `pide_codigo` | solicitud | Código de verificación, OTP, PIN, clave o contraseña |
| `pide_datos_bancarios` | solicitud | Número de tarjeta o cuenta, CVV, fecha de vencimiento |
| `pide_transferencia` | solicitud | Transferir, consignar o girar dinero |
| `acceso_remoto` | solicitud | Instalar AnyDesk, TeamViewer u otra app; compartir pantalla |
| `desactivar_seguridad` | solicitud | Desactivar alertas, verificación, antivirus o biometría |
| `urgencia` | presión | "Urgente", "ya mismo", "antes de que…" |
| `amenaza` | presión | Captura, embargo, bloqueo, demanda |
| `aislamiento` | presión | "No cuelgue", "no le diga a nadie" |
| `suplanta_entidad` | contexto | Dice llamar de un banco, la Fiscalía, la DIAN, un operador o una mensajería |
| `premio_inversion` | contexto | Premios, sorteos, inversiones garantizadas, créditos, devoluciones |
| `pide_datos_personales` | contexto | Cédula, fecha de nacimiento, dirección |

`GET /senales` devuelve esta misma lista para que la interfaz pueda explicar cada alerta.

Las solicitudes no cuentan cuando van precedidas de una advertencia como "nunca le pediremos su clave" o "no comparta su código", que es lo que dicen las entidades legítimas.

## Niveles de riesgo

Se calculan con reglas verificables. No se muestran porcentajes porque todavía no hay una validación estadística que los respalde.

| Nivel | Regla |
|---|---|
| Crítico | Una solicitud junto con alguna señal de presión |
| Alto | Una solicitud, o tres o más señales distintas de presión o contexto |
| Moderado | Al menos una señal de presión o contexto |
| Bajo | Ninguna señal |

Por defecto la alerta aparece desde el nivel **alto** (`CENTINELA_NIVEL_ALERTA`). Ese umbral se fijará con los datos de validación del paso 10.

## Mensaje de la alerta

Cada decisión trae un mensaje corto con el nivel, la razón más grave y qué hacer. Por ejemplo:

> RIESGO ALTO. Te piden un código o una clave. No lo hagas. Finaliza la llamada y verifica el contacto desde el canal oficial de la entidad.

El nivel bajo nunca dice que la llamada es segura, solo que no se encontraron señales. Cada decisión indica su `fuente`: `"contenido"` cuando sale solo de lo dicho, o `"contenido_y_reputacion"` cuando además pesa la señal `numero_reportado` ([reportes.md](reportes.md)). Ninguna decisión afirma una identidad confirmada. Desde el paso 11 la estrategia visible por defecto es la híbrida, que suma a estas reglas la señal `patron_aprendido` del [clasificador](clasificador.md).

## Criterios de aceptación

- [x] Cada señal de la sección 2.1 de la especificación tiene al menos una prueba.
- [x] Los cuatro niveles siguen las reglas de la tabla y tienen pruebas.
- [x] Una advertencia legítima ("nunca le pediremos su clave") no sube el riesgo.
- [x] Los mensajes no incluyen porcentajes ni prometen seguridad.
- [x] Las entradas vacías, demasiado largas o con tiempos inválidos se rechazan con 422.
- [x] Los registros del servidor no contienen el texto de la conversación.
- [x] Las dependencias tienen versión fija y se revisan con `pip-audit` en cada PR.

## Limitaciones

Son reglas de palabras clave. Un estafador que cambie el vocabulario puede evitarlas, y una llamada legítima que mencione "transferencia" puede subir a riesgo alto. El clasificador del paso 11 y la evaluación del paso 10 sirven para medir y reducir ambos errores.
