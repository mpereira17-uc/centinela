# Evaluación en modo texto (regional)

Generado por `python -m evaluacion.evaluar` el 2026-11-14. 12 guiones de [datos/guiones/guiones-regionales.json](../guiones/guiones-regionales.json). Solo se analizan los turnos de quien llama, como en la llamada simulada.

| Estrategia | Detección | IC 95 % | Falsas alertas | IC 95 % | Precisión | F1 | Demora (mediana) | Demora (p95) | Tardías |
|---|---|---|---|---|---|---|---|---|---|
| por_fragmento | 6/6 (100 %) | 61–100 % | 0/6 (0 %) | 0–39 % | 100 % | 100 % | 0,0 s | 0,0 s | 0/6 |
| acumulacion | 6/6 (100 %) | 61–100 % | 0/6 (0 %) | 0–39 % | 100 % | 100 % | 0,0 s | 0,0 s | 0/6 |
| clasificador | 6/6 (100 %) | 61–100 % | 0/6 (0 %) | 0–39 % | 100 % | 100 % | 0,0 s | 0,0 s | 0/6 |
| hibrida | 6/6 (100 %) | 61–100 % | 0/6 (0 %) | 0–39 % | 100 % | 100 % | 0,0 s | 0,0 s | 0/6 |

## Comparación llamada a llamada

Diferencia = segunda estrategia menos primera, en puntos porcentuales. El intervalo sale de remuestrear 2000 veces familias completas de llamadas (una plantilla con todas sus regiones cuenta como una sola), porque comparten la forma del engaño. Si el intervalo incluye el cero, la diferencia no es concluyente con estos guiones.

**por_fragmento → acumulacion**

- Detección (6 familias de riesgo): +0,0 pp (IC 95 %: +0,0 a +0,0). Solo acumulacion: ninguna; solo por_fragmento: ninguna.
- Falsas alertas (6 familias legítimas): +0,0 pp (IC 95 %: +0,0 a +0,0). Solo acumulacion: ninguna; solo por_fragmento: ninguna.
- Cuando ambas avisan: acumulacion avisa en un turno anterior en 0 llamadas y por_fragmento en 0.

**clasificador → hibrida**

- Detección (6 familias de riesgo): +0,0 pp (IC 95 %: +0,0 a +0,0). Solo hibrida: ninguna; solo clasificador: ninguna.
- Falsas alertas (6 familias legítimas): +0,0 pp (IC 95 %: +0,0 a +0,0). Solo hibrida: ninguna; solo clasificador: ninguna.
- Cuando ambas avisan: hibrida avisa en un turno anterior en 0 llamadas y clasificador en 0.


## Errores

- **por_fragmento**: no detectadas ninguna; falsas alertas ninguna; alertas anticipadas 0.
- **acumulacion**: no detectadas ninguna; falsas alertas ninguna; alertas anticipadas 0.
- **clasificador**: no detectadas ninguna; falsas alertas ninguna; alertas anticipadas 0.
- **hibrida**: no detectadas ninguna; falsas alertas ninguna; alertas anticipadas 0.

## Por guion

| Guion | Etiqueta | Categoría | por_fragmento | acumulacion | clasificador | hibrida |
|---|---|---|---|---|---|---|
| g01 | riesgo | suplanta_banco | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s |
| g02 | riesgo | familiar_falso | aviso en turno 3, 10,8 s | aviso en turno 3, 10,8 s | aviso en turno 3, 10,8 s | aviso en turno 3, 10,8 s |
| g03 | riesgo | extorsion | aviso en turno 1, 9,2 s | aviso en turno 1, 9,2 s | aviso en turno 1, 9,2 s | aviso en turno 1, 9,2 s |
| g04 | riesgo | soporte_falso | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| g05 | riesgo | premio_falso | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| g06 | riesgo | suplanta_entidad | aviso en turno 2, 11,2 s | aviso en turno 2, 11,2 s | aviso en turno 2, 11,2 s | aviso en turno 2, 11,2 s |
| g07 | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| g08 | legitima | banco | sin aviso | sin aviso | sin aviso | sin aviso |
| g09 | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| g10 | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| g11 | legitima | salud | sin aviso | sin aviso | sin aviso | sin aviso |
| g12 | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |

## Cómo leerlo

- La demora va desde que termina la primera petición riesgosa hasta el aviso. Es negativa si el aviso llega antes; es tardía si pasa de 5,0 s, valor fijado antes de probar. La mediana y el percentil 95 solo cuentan las llamadas detectadas; las no detectadas se listan aparte.
- Los tiempos de la tabla por guion se miden desde que empieza el turno con la solicitud de riesgo hasta que termina el turno que dispara el aviso; en modo texto, la duración de cada turno se estima a 2,5 palabras por segundo.
- Una alerta anticipada ocurre antes del turno anotado como solicitud de riesgo.
- Con tan pocos guiones los intervalos de confianza son anchos: sirven para comparar estrategias, no como cifra definitiva.
- Los guiones los escribió el mismo equipo que escribió las reglas; por eso la partición reservada se usa solo para el informe final.
