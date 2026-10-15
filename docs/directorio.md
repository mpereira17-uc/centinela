# Directorio de canales oficiales

La pantalla **Ayuda** (`/ayuda.html`) reúne los canales para verificar una llamada o un mensaje por tu cuenta: cuelga y contacta tú a la entidad por un canal que no te dio quien llamó. El aviso de riesgo de la pantalla principal enlaza aquí.

- Datos: [datos/directorio/directorio.json](../datos/directorio/directorio.json). API: `GET /directorio`, agrupado por tipo.
- Búsqueda sin tildes ("bogota" encuentra "Banco de Bogotá"). Cada entrada abre el teléfono (`tel:`) o la página oficial en otra pestaña; Centinela no llama ni escribe a nadie.

## Qué teléfonos se ponen

Solo los confirmados en fuentes oficiales:

| Línea | Para qué | Fuente |
|---|---|---|
| 123 | Emergencias y delitos en curso | [Alcaldía de Bogotá](https://bogota.gov.co/mi-ciudad/seguridad/conozca-como-puede-denunciar-la-extorsion-en-bogota-y-recibir-apoyo) |
| 165 | GAULA: extorsión y secuestro | [Alcaldía de Bogotá](https://bogota.gov.co/mi-ciudad/seguridad/conozca-como-puede-denunciar-la-extorsion-en-bogota-y-recibir-apoyo), [Policía](https://www.policia.gov.co/noticia/grupo-gaula-en-manizales-continua-invitando-comunidad-denunciar-extorsion-traves-linea-165) |
| 122 | Fiscalía: denuncias | [Canales de la Fiscalía](https://www.fiscalia.gov.co/colombia/noticias/canales-de-atencion-y-recepcion-de-denuncias-de-la-fiscalia-general-de-la-nacion/attachment/estos-son-los-canales-de-atencion-y-recepcion-de-denuncias-de-la-fiscalia-general-de-la-nacion/) |

**Los bancos y billeteras no llevan teléfono** a propósito. Sus números cambian, varían por ciudad y en internet hay muchos directorios no oficiales; un número equivocado aquí sería justo el error que Centinela quiere evitar. La app dice: "llama al número del respaldo de tu tarjeta o al de la aplicación oficial", y enlaza la página oficial del banco. Una prueba verifica que ninguna entrada de banco o billetera tenga teléfono.

## Coherencia con la revisión de enlaces

Cada página del directorio usa https y es un dominio que la [revisión de mensajes](mensajes.md) reconoce como oficial; una prueba lo comprueba. Así la app nunca enlaza una página que en otra pantalla marcaría como sospechosa.

## Mantenimiento

El archivo dice cuándo se revisó (`actualizado`) y la pantalla lo muestra. Antes de publicar en la Play Store hay que volver a revisar cada enlace.
