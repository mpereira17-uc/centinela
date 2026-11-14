# Evaluación en modo texto (desarrollo)

Generado por `python -m evaluacion.evaluar` el 2026-11-14. 24 guiones de [datos/guiones/guiones.json](../guiones/guiones.json). Solo se analizan los turnos de quien llama, como en la llamada simulada.

| Estrategia | Detección | IC 95 % | Falsas alertas | IC 95 % | Precisión | F1 | Demora (mediana) | Demora (p95) | Tardías |
|---|---|---|---|---|---|---|---|---|---|
| por_fragmento | 10/12 (83 %) | 55–95 % | 0/12 (0 %) | 0–24 % | 100 % | 91 % | 0,0 s | 0,0 s | 0/10 |
| acumulacion | 10/12 (83 %) | 55–95 % | 1/12 (8 %) | 1–35 % | 91 % | 87 % | 0,0 s | 0,0 s | 0/10 |
| clasificador | 12/12 (100 %) | 76–100 % | 0/12 (0 %) | 0–24 % | 100 % | 100 % | 0,0 s | 0,0 s | 0/12 |
| hibrida | 12/12 (100 %) | 76–100 % | 1/12 (8 %) | 1–35 % | 92 % | 96 % | 0,0 s | 0,0 s | 0/12 |

## Comparación llamada a llamada

Diferencia = segunda estrategia menos primera, en puntos porcentuales. El intervalo sale de remuestrear 2000 veces familias completas de llamadas (una plantilla con todas sus regiones cuenta como una sola), porque comparten la forma del engaño. Si el intervalo incluye el cero, la diferencia no es concluyente con estos guiones.

**por_fragmento → acumulacion**

- Detección (12 familias de riesgo): +0,0 pp (IC 95 %: +0,0 a +0,0). Solo acumulacion: ninguna; solo por_fragmento: ninguna.
- Falsas alertas (12 familias legítimas): +8,3 pp (IC 95 %: +0,0 a +25,0). Solo acumulacion: l06; solo por_fragmento: ninguna.
- Cuando ambas avisan: acumulacion avisa en un turno anterior en 0 llamadas y por_fragmento en 0.

**clasificador → hibrida**

- Detección (12 familias de riesgo): +0,0 pp (IC 95 %: +0,0 a +0,0). Solo hibrida: ninguna; solo clasificador: ninguna.
- Falsas alertas (12 familias legítimas): +8,3 pp (IC 95 %: +0,0 a +25,0). Solo hibrida: l06; solo clasificador: ninguna.
- Cuando ambas avisan: hibrida avisa en un turno anterior en 0 llamadas y clasificador en 0.


## Errores

- **por_fragmento**: no detectadas r06, r09; falsas alertas ninguna; alertas anticipadas 0.
- **acumulacion**: no detectadas r06, r09; falsas alertas l06; alertas anticipadas 0.
- **clasificador**: no detectadas ninguna; falsas alertas ninguna; alertas anticipadas 0.
- **hibrida**: no detectadas ninguna; falsas alertas l06; alertas anticipadas 0.

## Por guion

| Guion | Etiqueta | Categoría | por_fragmento | acumulacion | clasificador | hibrida |
|---|---|---|---|---|---|---|
| r01 | riesgo | suplanta_banco | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s |
| r02 | riesgo | suplanta_banco | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| r03 | riesgo | familiar_falso | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s |
| r04 | riesgo | soporte_falso | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s |
| r05 | riesgo | premio_falso | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s |
| r06 | riesgo | extorsion | sin aviso | sin aviso | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s |
| r07 | riesgo | suplanta_entidad | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s |
| r08 | riesgo | inversion_falsa | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s |
| r09 | riesgo | suplanta_banco | sin aviso | sin aviso | aviso en turno 2, 5,2 s | aviso en turno 2, 5,2 s |
| r10 | riesgo | envio_falso | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s |
| r11 | riesgo | empleo_falso | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s |
| r12 | riesgo | suplanta_entidad | aviso en turno 2, 5,2 s | aviso en turno 2, 5,2 s | aviso en turno 2, 5,2 s | aviso en turno 2, 5,2 s |
| l01 | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| l02 | legitima | cita_medica | sin aviso | sin aviso | sin aviso | sin aviso |
| l03 | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| l04 | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| l05 | legitima | telefonia | sin aviso | sin aviso | sin aviso | sin aviso |
| l06 | legitima | banco_real | sin aviso | aviso en turno 3 | sin aviso | aviso en turno 3 |
| l07 | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| l08 | legitima | encuesta | sin aviso | sin aviso | sin aviso | sin aviso |
| l09 | legitima | colegio | sin aviso | sin aviso | sin aviso | sin aviso |
| l10 | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| l11 | legitima | amistad | sin aviso | sin aviso | sin aviso | sin aviso |
| l12 | legitima | salud | sin aviso | sin aviso | sin aviso | sin aviso |

## Cómo leerlo

- La demora va desde que termina la primera petición riesgosa hasta el aviso. Es negativa si el aviso llega antes; es tardía si pasa de 5,0 s, valor fijado antes de probar. La mediana y el percentil 95 solo cuentan las llamadas detectadas; las no detectadas se listan aparte.
- Los tiempos de la tabla por guion se miden desde que empieza el turno con la solicitud de riesgo hasta que termina el turno que dispara el aviso; en modo texto, la duración de cada turno se estima a 2,5 palabras por segundo.
- Una alerta anticipada ocurre antes del turno anotado como solicitud de riesgo.
- Con tan pocos guiones los intervalos de confianza son anchos: sirven para comparar estrategias, no como cifra definitiva.
- Los guiones los escribió el mismo equipo que escribió las reglas; por eso la partición reservada se usa solo para el informe final.
