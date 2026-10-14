# Modelo de amenazas

Modelo inicial de la beta descrita en [viabilidad.md](viabilidad.md). Usa STRIDE sobre los componentes de la beta y añade las amenazas propias de un sistema de IA y de reportes comunitarios. Se actualiza en cada paso de la [hoja de ruta](hoja-de-ruta.md); la columna **Estado** dice si la mitigación ya está en el código.

## 1. Qué protegemos

| Activo | Por qué importa |
|---|---|
| Audio y transcripciones de conversaciones | Pueden contener datos bancarios, códigos y datos de terceros |
| Historial de alertas | Revela con quién habla el usuario y de qué |
| Credenciales: passkeys, PIN, tokens de sesión | Dan acceso a todo lo anterior |
| Reportes de números | Pueden perjudicar a una persona si son falsos |
| Modelo de detección y sus reglas | Si se manipulan, dejan pasar fraudes o generan falsas alertas |
| Confianza del usuario en las alertas | Una alerta injustificada o ausente lleva a una mala decisión |

## 2. Actores

- **Estafador** que conoce Centinela y adapta su guion para no activar alertas.
- **Atacante remoto** que ataca la API: fuerza bruta, robo de sesión, inyección.
- **Persona con acceso al dispositivo**: robo o préstamo del celular.
- **Usuario malintencionado** que reporta números para perjudicar a alguien.
- **Proveedor o dependencia comprometida**: una librería o un modelo descargado con código malicioso.

## 3. Componentes y fronteras de confianza

```
[Navegador del usuario] --HTTPS--> [API FastAPI] --> [Motor de señales + clasificador]
        |                               |--> [Transcripción local (faster-whisper)]
   micrófono                            |--> [Base de datos SQLite]
                                        '--> [Voz sintética local (Piper)]
```

Las fronteras de confianza son el navegador frente a la API (todo lo que llega del navegador se valida) y la API frente a los datos guardados. Ningún dato sale del equipo hacia servicios de IA externos.

## 4. Matriz de amenazas y mitigaciones

| # | Amenaza | STRIDE | Componente | Mitigación | Estado |
|---|---|---|---|---|---|
| A1 | Fuerza bruta o *credential stuffing* contra el PIN | Suplantación | API | Límite de intentos con bloqueo temporal; PIN guardado con Argon2; passkeys como opción preferida | Paso 6 |
| A2 | Robo o reutilización del token de sesión | Suplantación | API, navegador | Cookie `HttpOnly`, `Secure` y `SameSite=Strict`; expiración corta; revocación desde "Dispositivos y sesiones" | Paso 6 |
| A3 | Repetición de solicitudes sensibles | Manipulación | API | Retos de un solo uso en WebAuthn; tokens CSRF en formularios | Paso 6 |
| A4 | Inyección SQL | Manipulación | Base de datos | Solo consultas parametrizadas mediante el ORM | Paso 7 |
| A5 | XSS al mostrar una transcripción en la interfaz | Manipulación | Navegador | Insertar el texto con `textContent`, nunca como HTML; política CSP estricta | Hecho (paso 3) |
| A6 | Entradas enormes o malformadas que tumban el servicio | Denegación de servicio | API | Validación con Pydantic, límites de tamaño de texto y audio, límite de solicitudes por cliente | Límites de tamaño hechos (pasos 2 y 4); límite por cliente en el paso 6 |
| A7 | Acceso a llamadas o alertas de otro usuario | Elevación de privilegios | API | Autorización en el servidor en cada consulta, por dueño del recurso | Paso 6 |
| A8 | Fuga de transcripciones o códigos en los logs | Divulgación | API | No registrar texto de conversaciones, PIN, tokens ni audio; registrar solo identificadores y decisiones | Hecho (paso 2) |
| A9 | Audio guardado sin que el usuario lo sepa | Divulgación | Transcripción | El audio se procesa en memoria y se descarta; guardarlo exige consentimiento explícito | Hecho (paso 4) |
| A10 | Datos que quedan después de que el usuario pide borrarlos | Divulgación | Base de datos | Borrado real en cascada; retención limitada del historial | Paso 7 |
| A11 | Estafador que reformula su guion para evadir las reglas | Manipulación | Motor | Acumular indicios a lo largo de la llamada; clasificador entrenado con variaciones; evaluar con guiones nuevos | Acumulación hecha (paso 2); clasificador en el paso 11 |
| A12 | Inyección de instrucciones en el texto analizado ("ignora lo anterior...") | Manipulación | Motor | El motor no usa un modelo de lenguaje que siga instrucciones; el texto solo se clasifica | Por diseño |
| A13 | Falsa alerta en una llamada legítima | — | Motor | Niveles con razones visibles; sin porcentajes no calibrados; un solo aviso por llamada; medir falsas alertas | Hecho (paso 2); medición en el paso 10 |
| A14 | Sesgo por acento, género o edad de quien habla | — | Motor | El motor decide sobre el contenido, no sobre la voz; revisar errores de transcripción por grupo en la evaluación | Por diseño, paso 10 |
| A15 | Reportes falsos o coordinados contra un número | Manipulación | Reportes | Límite de reportes por cuenta; la reputación pesa como señal y nunca decide sola; separar "reportado" de "confirmado" | Paso 8 |
| A16 | Exposición de quién reportó | Divulgación | Reportes | Reportes seudónimos; no se publican datos del denunciante | Paso 8 |
| A17 | Voz clonada que imita a un familiar | Suplantación | Usuario | La app nunca confirma una identidad por la voz; recomienda verificar por un canal independiente | Hecho (paso 5) |
| A18 | Orden de voz que desactiva la protección o revela datos | Elevación de privilegios | Asistente | La voz solo consulta; las acciones sensibles piden confirmación en pantalla con passkey o PIN | Bloqueo por voz hecho (paso 5); confirmación con PIN en el paso 6 |
| A19 | Dependencia o modelo descargado comprometido | Manipulación | Servidor | Versiones fijadas; modelos solo de fuentes oficiales; revisión de dependencias con `pip-audit` | Hecho (paso 2) |
| A20 | Afirmar que se bloqueó algo que la app no puede bloquear | — | Interfaz | Los textos solo prometen lo que el sistema hace; revisión de mensajes en cada paso | Todos |

## 5. Riesgos aceptados en la beta

- La beta corre en un portátil, sin copias de seguridad cifradas ni separación de ambientes de producción. Es aceptable porque solo maneja datos de prueba de voluntarios con consentimiento.
- No hay pruebas de penetración independientes; se compensa con las pruebas automatizadas de cada paso y la revisión con OWASP ASVS nivel 1.
- La biometría vocal y la detección de clonación no se implementan, así que sus amenazas (muestras manipuladas, ataques de repetición de voz) quedan para cuando se evalúe su viabilidad.

## 6. Referencias

- OWASP ASVS 4.0, nivel 1, para los controles del backend.
- OWASP API Security Top 10 (2023).
- OWASP MASVS, para cuando exista una app nativa.
- Ley 1581 de 2012 y Decreto 1377 de 2013, sobre datos sensibles y consentimiento.
