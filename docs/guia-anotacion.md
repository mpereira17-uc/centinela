# Guía de anotación de guiones

Reglas para escribir y etiquetar los guiones de [datos/guiones/guiones.json](../datos/guiones/guiones.json). Centinela identifica **solicitudes de riesgo** según esta guía; una etiqueta no afirma que una persona haya cometido un delito.

## Etiqueta de la llamada

| Etiqueta | Cuándo |
|---|---|
| `riesgo` | Quien llama pide algo que permite quitarle dinero o el control de una cuenta a quien recibe: códigos o claves, datos de tarjeta, una transferencia o pago, instalar una aplicación de acceso remoto o desactivar protecciones. También las amenazas para obtener dinero |
| `legitima` | No hay ninguna de esas solicitudes, aunque se mencione un banco, una urgencia, un código que **no** se pide compartir o un premio que no cuesta nada |

## Turno de riesgo

`turno_riesgo` es el índice (desde 0) del **primer turno de quien llama** con la solicitud. Las llamadas legítimas lo dejan en `null`. Sirve para medir el tiempo de aviso: desde que empieza ese turno hasta que Centinela avisa.

## Partición

- `desarrollo`: se puede leer y usar para ajustar las reglas o entrenar el clasificador.
- `reservada`: solo para el informe final. No se miran sus errores para cambiar reglas ni modelos; si se hace, deja de ser reservada y hay que escribir guiones nuevos.

Cada partición tiene el mismo número de llamadas de riesgo y legítimas.

## Cómo escribir un guion

- Español colombiano coloquial, frases como se dirían en una llamada.
- Datos inventados: nunca números de cuenta, cédulas ni teléfonos reales.
- Incluir **casos difíciles**: llamadas legítimas que se parecen a una estafa (el banco que habla de seguridad sin pedir nada, un premio real sin costo, una urgencia familiar sin dinero) y estafas que evitan las palabras típicas ("léame los seis números que le llegaron").
- `categoria` describe el tipo de llamada (por ejemplo `suplanta_banco`, `familiar_falso`, `cita_medica`) para analizar errores por tipo.
- `descripcion` resume el guion en una línea.

## Formato

```json
{
  "id": "r01", "etiqueta": "riesgo", "categoria": "suplanta_banco", "particion": "desarrollo",
  "descripcion": "Falso empleado del banco pide el código de verificación",
  "turno_riesgo": 3,
  "turnos": [["llamante", "Buenas tardes..."], ["usuario", "Sí, con él..."]]
}
```

`backend/tests/test_evaluacion.py` valida el formato, que el turno de riesgo sea de quien llama y que las particiones estén balanceadas.
