# Evaluación en modo texto (reservada)

Generado por `python -m evaluacion.evaluar` el 2026-10-15. 12 guiones de [datos/guiones/guiones.json](../guiones/guiones.json). Solo se analizan los turnos de quien llama, como en la llamada simulada.

| Estrategia | Detección | IC 95 % | Falsas alertas | IC 95 % | Precisión | Aviso (mediana) | Aviso (máx.) |
|---|---|---|---|---|---|---|---|
| por_fragmento | 3/6 (50 %) | 19–81 % | 1/6 (17 %) | 3–56 % | 75 % | 6,4 s | 7,6 s |
| acumulacion | 3/6 (50 %) | 19–81 % | 1/6 (17 %) | 3–56 % | 75 % | 6,4 s | 7,6 s |
| clasificador | 6/6 (100 %) | 61–100 % | 1/6 (17 %) | 3–56 % | 86 % | 2,8 s | 7,6 s |
| hibrida | 6/6 (100 %) | 61–100 % | 1/6 (17 %) | 3–56 % | 86 % | 2,8 s | 7,6 s |

## Errores

- **por_fragmento**: no detectadas r14, r15, r18; falsas alertas l13; alertas anticipadas 0.
- **acumulacion**: no detectadas r14, r15, r18; falsas alertas l13; alertas anticipadas 0.
- **clasificador**: no detectadas ninguna; falsas alertas l13; alertas anticipadas 3.
- **hibrida**: no detectadas ninguna; falsas alertas l13; alertas anticipadas 3.

## Por guion

| Guion | Etiqueta | Categoría | por_fragmento | acumulacion | clasificador | hibrida |
|---|---|---|---|---|---|---|
| r13 | riesgo | suplanta_banco | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s |
| r14 | riesgo | familiar_falso | sin aviso | sin aviso | aviso en turno 2, 0,0 s | aviso en turno 2, 0,0 s |
| r15 | riesgo | soporte_falso | sin aviso | sin aviso | aviso en turno 1, 0,0 s | aviso en turno 1, 0,0 s |
| r16 | riesgo | premio_falso | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 0, 0,0 s | aviso en turno 0, 0,0 s |
| r17 | riesgo | extorsion | aviso en turno 1, 7,6 s | aviso en turno 1, 7,6 s | aviso en turno 1, 7,6 s | aviso en turno 1, 7,6 s |
| r18 | riesgo | suplanta_banco | sin aviso | sin aviso | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s |
| l13 | legitima | banco_real | aviso en turno 1 | aviso en turno 1 | aviso en turno 1 | aviso en turno 1 |
| l14 | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| l15 | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| l16 | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| l17 | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| l18 | legitima | vecinos | sin aviso | sin aviso | sin aviso | sin aviso |

## Cómo leerlo

- Los tiempos se miden desde que empieza el turno con la solicitud de riesgo hasta que termina el turno que dispara el aviso; en modo texto, la duración de cada turno se estima a 2,5 palabras por segundo.
- Una alerta anticipada ocurre antes del turno anotado como solicitud de riesgo.
- Con tan pocos guiones los intervalos de confianza son anchos: sirven para comparar estrategias, no como cifra definitiva.
- Los guiones los escribió el mismo equipo que escribió las reglas; por eso la partición reservada se usa solo para el informe final.
