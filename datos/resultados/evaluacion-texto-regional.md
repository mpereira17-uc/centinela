# Evaluación en modo texto (regional)

Generado por `python -m evaluacion.evaluar` el 2026-10-15. 12 guiones de [datos/guiones/guiones-regionales.json](../guiones/guiones-regionales.json). Solo se analizan los turnos de quien llama, como en la llamada simulada.

| Estrategia | Detección | IC 95 % | Falsas alertas | IC 95 % | Precisión | Aviso (mediana) | Aviso (máx.) |
|---|---|---|---|---|---|---|---|
| por_fragmento | 6/6 (100 %) | 61–100 % | 0/6 (0 %) | 0–39 % | 100 % | 9,2 s | 11,2 s |
| acumulacion | 6/6 (100 %) | 61–100 % | 0/6 (0 %) | 0–39 % | 100 % | 9,2 s | 11,2 s |
| clasificador | 6/6 (100 %) | 61–100 % | 0/6 (0 %) | 0–39 % | 100 % | 9,2 s | 11,2 s |
| hibrida | 6/6 (100 %) | 61–100 % | 0/6 (0 %) | 0–39 % | 100 % | 9,2 s | 11,2 s |

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

- Los tiempos se miden desde que empieza el turno con la solicitud de riesgo hasta que termina el turno que dispara el aviso; en modo texto, la duración de cada turno se estima a 2,5 palabras por segundo.
- Una alerta anticipada ocurre antes del turno anotado como solicitud de riesgo.
- Con tan pocos guiones los intervalos de confianza son anchos: sirven para comparar estrategias, no como cifra definitiva.
- Los guiones los escribió el mismo equipo que escribió las reglas; por eso la partición reservada se usa solo para el informe final.
