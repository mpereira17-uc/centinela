# Especificación original de pepe

Texto escrito por pepe y compartido en el proyecto el 2026-10-14. Se conserva tal cual; el alcance real de la beta de tesis está en `docs/viabilidad.md` y `docs/hoja-de-ruta.md`.

---

DESARROLLO DE UNA APP MÓVIL DE CIBERSEGURIDAD, DETECCIÓN DE ESTAFAS TELEFÓNICAS E IDENTIDAD VOCAL

## 1. Rol y objetivo del proyecto

Actúa como un equipo multidisciplinario compuesto por arquitectos de software, desarrolladores móviles, especialistas en ciberseguridad, expertos en inteligencia artificial, ingenieros de procesamiento de voz, diseñadores UX/UI y especialistas en protección de datos personales.

Diseña y desarrolla una aplicación móvil de seguridad personal que proteja al usuario contra llamadas fraudulentas, suplantación de identidad, ingeniería social, phishing telefónico, extorsiones, fraudes financieros y clonación de voz mediante inteligencia artificial.

La aplicación debe funcionar como un asistente de seguridad en tiempo real, capaz de advertir al usuario cuando una llamada presente indicios de fraude, explicar los riesgos detectados y ofrecer acciones concretas para prevenir pérdidas económicas o el robo de información.

La voz del usuario debe ser un componente esencial de la aplicación, tanto para interactuar con ella como para implementar mecanismos opcionales de autenticación y protección de identidad vocal.

La aplicación no debe prometer una detección infalible. Debe comunicar niveles de riesgo, incertidumbre y limitaciones técnicas de manera transparente.

## 2. Funcionalidades principales

### 2.1. Detección de estafas durante llamadas

Implementar un sistema de análisis de llamadas que, cuando el sistema operativo y los permisos lo permitan, pueda identificar señales de riesgo como:

* Llamadas que se hacen pasar por bancos, entidades gubernamentales, empresas de mensajería, operadores telefónicos o servicios técnicos.
* Solicitudes de contraseñas, códigos OTP, PIN, datos bancarios o credenciales.
* Presión psicológica, amenazas, urgencia artificial o exigencias de transferencias inmediatas.
* Supuestos premios, inversiones garantizadas, créditos fraudulentos o devolución de impuestos.
* Solicitudes para instalar aplicaciones de acceso remoto.
* Instrucciones para desactivar mecanismos de seguridad.
* Intentos de obtener información personal mediante preguntas aparentemente inocentes.
* Números telefónicos asociados con reportes de fraude, cuando exista una fuente verificable.
* Patrones de conversación compatibles con ingeniería social.

Cuando se detecte una señal relevante, mostrar una alerta clara, por ejemplo:
"POSIBLE ESTAFA: la persona solicita un código de verificación. No lo compartas. Cuelga y comunícate con la entidad mediante su canal oficial".

La aplicación debe distinguir entre una sospecha basada en el contenido de la conversación, un número reportado por terceros y una identidad confirmada. No debe declarar culpable a una persona únicamente por su número telefónico.

### 2.2. Análisis inteligente de conversaciones

Diseñar un motor de análisis basado en inteligencia artificial que pueda procesar, si existe autorización y capacidad técnica:

* Transcripciones de voz a texto.
* Palabras y frases de alto riesgo.
* Contexto semántico de la conversación.
* Solicitudes de dinero o información confidencial.
* Cambios repentinos en las instrucciones.
* Manipulación emocional y presión temporal.
* Instrucciones para evadir los procedimientos de seguridad.
* Inconsistencias entre la identidad declarada y las acciones solicitadas.

El análisis debe priorizar la detección de conductas fraudulentas y no el acento, género, edad, nacionalidad o características personales de quien habla.

El sistema debe generar un nivel de riesgo comprensible:

* Riesgo bajo: no se identifican señales relevantes.
* Riesgo moderado: existen comportamientos que requieren precaución.
* Riesgo alto: se identifican solicitudes o patrones fuertemente asociados con fraude.
* Riesgo crítico: se detectan indicios de una acción inmediata de alto impacto, como la entrega de credenciales o una transferencia inducida bajo engaño.

Estos niveles deben calcularse mediante criterios verificables y calibrados. No se deben mostrar porcentajes de certeza si no existe una validación estadística que los respalde.

### 2.3. La voz del usuario como función esencial

La voz debe formar parte central de la experiencia. Implementar las siguientes capacidades:

**A. Asistente por voz.** El usuario podrá decir comandos como:

* "Analiza esta llamada".
* "¿Esta llamada parece una estafa?".
* "Explícame la alerta".
* "Activa mi protección".
* "Quiero reportar este número".
* "Ayúdame a verificar la identidad de esta persona".

La aplicación debe responder mediante voz sintetizada y mostrar simultáneamente información visual.

**B. Autenticación vocal opcional.** Permitir que el usuario registre voluntariamente muestras de su voz para crear una referencia biométrica protegida, siempre que el dispositivo y la infraestructura soporten esta función de forma segura. Esta referencia podrá utilizarse como factor adicional de autenticación, nunca como único mecanismo para autorizar operaciones financieras o acciones de alto riesgo. Incorporar:

* Consentimiento explícito y revocable.
* Detección de reproducción de grabaciones y ataques de repetición.
* Evaluación de intentos de suplantación mediante voz sintética.
* Protección frente a muestras manipuladas.
* Autenticación alternativa mediante PIN, passkeys o biometría del sistema operativo.
* Límites de intentos, bloqueos temporales y notificaciones ante actividad sospechosa.
* Procedimientos de recuperación de cuenta que no dependan exclusivamente de la voz.

La aplicación no debe asumir que una voz familiar garantiza la identidad de quien llama. La clonación vocal mediante IA puede imitar voces legítimas.

**C. Detección de posible clonación de voz.** Cuando sea técnicamente viable, evaluar señales de voz sintética, manipulación o reproducción artificial. Combinar el resultado con contexto conversacional y otros indicadores. Advertir expresamente que los detectores de voz sintética pueden equivocarse y que no existe una garantía universal de detección.

**D. Confirmación de acciones sensibles.** Antes de realizar una acción importante, como cambiar credenciales, compartir información o modificar ajustes críticos, solicitar una confirmación segura independiente del comando de voz. La voz por sí sola no debe autorizar transferencias, revelar secretos ni desactivar protecciones.

## 3. Registro seguro y gestión de cuentas

Implementar un registro sencillo, seguro y respetuoso con la privacidad.

Opciones de acceso:

* Passkeys cuando sean compatibles.
* Autenticación biométrica nativa del dispositivo.
* PIN seguro como alternativa.
* Correo electrónico verificado, si resulta necesario.
* Autenticación multifactor para operaciones sensibles.

Requisitos:

* Recopilar únicamente los datos estrictamente necesarios.
* No exigir una grabación de voz para utilizar las funciones básicas de protección.
* Solicitar consentimiento separado para cada finalidad biométrica.
* Explicar qué información se almacena, durante cuánto tiempo y para qué se utiliza.
* Permitir consultar, descargar y eliminar los datos personales.
* Permitir eliminar la cuenta y revocar sesiones activas.
* No almacenar contraseñas en texto plano.
* No almacenar códigos OTP después de su uso.
* No utilizar preguntas de seguridad basadas en información pública.
* No exponer datos personales en mensajes de error, registros técnicos o notificaciones.

La autenticación biométrica nativa debe preferirse cuando sea suficiente, evitando crear una base centralizada de huellas, rostros o voces sin necesidad demostrada.

## 4. Arquitectura de seguridad

Diseñar una arquitectura con seguridad desde el inicio y siguiendo principios de mínimo privilegio, defensa en profundidad y privacidad por diseño.

**Seguridad del dispositivo**

* Integración con los mecanismos seguros de Android e iOS.
* Uso de Android Keystore y Secure Enclave o Keychain, según disponibilidad.
* Protección de tokens y claves criptográficas.
* Detección de riesgos de integridad del dispositivo cuando sea pertinente.
* Manejo seguro de sesiones.
* Bloqueo automático de información sensible.
* Protección de datos mostrados en segundo plano cuando sea viable.
* Detección de versiones vulnerables de la aplicación.
* Actualizaciones seguras y verificadas.
* Restricción de permisos innecesarios.

No bloquear automáticamente todos los dispositivos modificados; evaluar el riesgo y limitar las operaciones sensibles de manera proporcional.

**Seguridad de las comunicaciones**

* HTTPS con TLS actualizado.
* Validación estricta de certificados.
* Protección contra ataques de intermediario.
* Gestión segura de claves.
* Renovación y revocación de tokens.
* Protección contra repetición de solicitudes.
* Autorización en el servidor para cada operación sensible.
* Límites de solicitudes y controles contra automatización abusiva.

No depender exclusivamente del certificado del cliente, de un secreto incluido en la aplicación o de controles ejecutados únicamente en el dispositivo.

**Seguridad del backend**

* Separación entre autenticación, análisis de llamadas, biometría y administración.
* Control de acceso basado en roles y atributos cuando corresponda.
* Principio de mínimo privilegio.
* Validación de entradas.
* Protección contra inyección SQL, XSS, CSRF y SSRF, según la superficie de ataque.
* Consultas parametrizadas.
* Gestión segura de secretos.
* Segmentación de servicios.
* Cifrado de datos en tránsito y en reposo.
* Copias de seguridad cifradas y pruebas de recuperación.
* Monitoreo de actividad sospechosa.
* Registros de auditoría con minimización de datos.
* Protección contra abuso de API y denegación de servicio.
* Separación de ambientes de desarrollo, pruebas y producción.

No registrar contraseñas, tokens, transcripciones completas ni muestras biométricas en logs.

## 5. Privacidad y protección de datos personales

Adoptar un enfoque de privacidad por defecto.

* Procesar audio localmente siempre que sea técnicamente viable.
* No grabar llamadas de manera oculta.
* No almacenar audio de forma permanente por defecto.
* Solicitar autorización expresa antes de transmitir audio a servicios externos.
* Separar el consentimiento para análisis de llamadas, transcripción, entrenamiento de modelos y autenticación vocal.
* No reutilizar datos de voz para entrenar modelos sin una autorización independiente y válida.
* Permitir borrar grabaciones, transcripciones y referencias biométricas.
* Definir periodos de retención limitados.
* Anonimizar o seudonimizar los datos de análisis cuando corresponda.
* Evitar enviar datos sensibles a proveedores de IA innecesarios.
* Evaluar los riesgos de transferencias internacionales de datos.
* Proporcionar una política de privacidad comprensible.
* Implementar procedimientos para solicitudes de acceso, corrección y supresión de información.

Para Colombia, evaluar el cumplimiento de la Ley 1581 de 2012, sus normas reglamentarias y las disposiciones aplicables al tratamiento de datos sensibles, incluidos los biométricos. Analizar también las obligaciones que correspondan según el servicio, el tratamiento de llamadas y los proveedores utilizados.

## 6. Compatibilidad real con Android e iOS

Diseñar las funciones teniendo en cuenta las restricciones reales de cada plataforma.

Antes de implementar el análisis de llamadas, verificar qué capacidades permiten Android e iOS para identificar llamadas, filtrar números, acceder a audio, utilizar servicios de accesibilidad y ejecutar procesos en segundo plano.

No asumir que una aplicación ordinaria puede escuchar libremente el audio de una llamada celular en curso.

Cuando el acceso directo al audio no esté disponible, ofrecer alternativas seguras:

* Identificación de números mediante las interfaces autorizadas del sistema operativo.
* Listas de números reportados y reputación telefónica.
* Análisis de mensajes de texto o enlaces sospechosos con autorización.
* Análisis de conversaciones mediante una transcripción aportada voluntariamente por el usuario.
* Activación de un asistente de voz independiente.
* Integración con mecanismos oficiales de filtrado de llamadas.

No grabar ni interceptar comunicaciones mediante métodos que vulneren los permisos, las políticas de las tiendas o la legislación aplicable.

## 7. Detección de fraudes mediante múltiples señales

Crear un motor de evaluación de riesgos que combine, cuando estén disponibles:

1. Reputación del número.
2. Reportes de otros usuarios, ponderados según su calidad.
3. Contenido de la conversación.
4. Solicitudes de dinero, contraseñas o códigos.
5. Contexto temporal y patrones de presión.
6. Señales de manipulación vocal.
7. Inconsistencias de identidad.
8. Indicadores de enlaces maliciosos.
9. Confirmación independiente de la entidad supuestamente representada.

Cada alerta debe mostrar las razones principales que la generaron, su nivel de confianza y las limitaciones relevantes.

Implementar mecanismos para reducir falsos positivos, prevenir reportes maliciosos y corregir clasificaciones erróneas.

La reputación de un número debe tratarse como una señal, no como una prueba concluyente.

## 8. Protección frente a ataques específicos

Evaluar y mitigar:

* Phishing y smishing.
* Vishing y suplantación telefónica.
* Clonación de voz.
* Robo de sesión.
* Credential stuffing.
* Ataques de fuerza bruta.
* Reutilización de tokens.
* Ataques de repetición.
* Ingeniería social.
* Manipulación de solicitudes.
* Exposición accidental de información.
* Malware y aplicaciones superpuestas maliciosas.
* Abuso de permisos.
* Extracción de datos locales.
* Manipulación de respuestas del servidor.
* Ataques contra modelos de IA.
* Inyección de instrucciones en contenido analizado.
* Envenenamiento de datos de reputación.
* Abuso de los mecanismos de denuncia.
* Ataques contra los flujos de recuperación de cuenta.
* Fraude mediante deepfakes de voz.

Incorporar modelado de amenazas, análisis de riesgos y pruebas de penetración independientes.

## 9. Interfaz y experiencia del usuario

Crear una interfaz moderna, accesible y de fácil comprensión para personas con distintos niveles de conocimientos tecnológicos.

Pantallas principales:

1. Inicio y estado de protección.
2. Registro e inicio de sesión.
3. Configuración de voz y permisos.
4. Protección de llamadas.
5. Historial de alertas.
6. Análisis detallado de riesgos.
7. Verificación segura de entidades.
8. Gestión de identidad vocal.
9. Privacidad y datos personales.
10. Dispositivos y sesiones activas.
11. Reporte de estafas.
12. Centro de ayuda y respuesta ante incidentes.

Utilizar señales visuales y sonoras accesibles para identificar niveles de riesgo, sin depender exclusivamente del color.

Las alertas deben ser breves, legibles y accionables. Por ejemplo:
"RIESGO ALTO. Te solicitan un código de verificación. No lo compartas. Finaliza la llamada y verifica el contacto desde la aplicación oficial de tu banco".

No mostrar alertas invasivas sin fundamento ni interrumpir innecesariamente llamadas legítimas.

## 10. Reportes y protección comunitaria

Permitir reportar números sospechosos y patrones de fraude sin publicar información personal de las víctimas.

Implementar:

* Reportes anónimos o seudónimos cuando sea posible.
* Moderación de denuncias.
* Detección de reportes coordinados.
* Eliminación o corrección de reportes erróneos.
* Fuentes de reputación verificables.
* Protección contra la exposición de datos de denunciantes.
* Límites de envío y mecanismos contra el abuso.
* Separación entre denuncias no verificadas y fraudes confirmados.

No permitir que un usuario utilice la plataforma para acosar, identificar públicamente o perjudicar a una persona basándose en acusaciones no verificadas.

## 11. Respuesta ante incidentes

Crear procedimientos para los siguientes escenarios:

* Pérdida o robo del dispositivo.
* Acceso no autorizado a una cuenta.
* Filtración de información.
* Robo de credenciales.
* Suplantación de voz.
* Uso fraudulento de la identidad del usuario.
* Falso positivo que perjudique a un usuario legítimo.
* Vulnerabilidad crítica en la aplicación.
* Compromiso de un proveedor de inteligencia artificial.

La aplicación debe permitir revocar sesiones, bloquear temporalmente funciones sensibles, cambiar credenciales, eliminar datos y consultar instrucciones de recuperación.

Si el usuario informa de una posible estafa bancaria, orientar hacia los canales oficiales de la entidad correspondiente y recomendar el bloqueo oportuno de productos cuando proceda.

No afirmar que se ha bloqueado una llamada, una cuenta bancaria o una transferencia si la aplicación no tiene capacidad real para ejecutar esa acción.

## 12. Desarrollo, pruebas y estándares

Utilizar un proceso de desarrollo seguro basado en:

* OWASP MASVS para seguridad de aplicaciones móviles.
* OWASP ASVS para controles de seguridad del backend.
* OWASP API Security Top 10 para riesgos de API.
* Pruebas automatizadas y manuales.
* Análisis estático y dinámico.
* Gestión de dependencias y vulnerabilidades.
* Firma y distribución segura de versiones.
* Revisión de permisos.
* Pruebas de privacidad.
* Pruebas de accesibilidad.
* Evaluación de precisión del sistema de IA.
* Pruebas adversariales de clonación vocal.
* Pruebas de falsos positivos y falsos negativos.
* Plan de divulgación responsable de vulnerabilidades.

Definir métricas para medir la tasa de detección de fraude, falsos positivos, latencia de alertas, consumo de batería, protección de datos y usabilidad.

## 13. Entregables solicitados

Desarrollar el proyecto por fases y presentar:

1. Nombre, identidad y propuesta de valor de la aplicación.
2. Requisitos funcionales y no funcionales.
3. Arquitectura técnica y diagramas.
4. Matriz de amenazas y mitigaciones.
5. Modelo de datos con información estrictamente necesaria.
6. Diseño de interfaces y prototipo navegable.
7. Estrategia de autenticación y protección biométrica.
8. Diseño del motor de detección de estafas.
9. Estrategia de compatibilidad Android/iOS.
10. Backend y API con controles de seguridad.
11. Plan de pruebas y validación.
12. Política de privacidad y gestión de consentimientos.
13. Plan de despliegue y mantenimiento.
14. Estimación de costos de infraestructura y servicios de IA.
15. Hoja de ruta de desarrollo por etapas.

Para cada funcionalidad, identificar qué es viable actualmente, qué requiere permisos o integraciones especiales y qué depende de servicios externos.

## 14. Instrucción final

No construyas únicamente una interfaz visual ni presentes funcionalidades simuladas como si fueran reales.

Comienza con un análisis de viabilidad técnica y un modelo de amenazas. Después, define un producto mínimo viable (MVP) que incluya registro seguro, asistente por voz, identificación de llamadas compatible con el sistema operativo, evaluación de señales de fraude y alertas comprensibles.

Implementa las funciones avanzadas de análisis de audio, biometría vocal y detección de clonación solo después de verificar su viabilidad, privacidad, seguridad y precisión.

Cada funcionalidad debe contar con criterios de aceptación, pruebas, manejo de errores y documentación.

El resultado debe ser una aplicación útil, segura, accesible y escalable, cuyo propósito principal sea prevenir que el usuario sea engañado durante una llamada y ayudarlo a tomar decisiones informadas sin exponer innecesariamente su información personal.
