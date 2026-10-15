# Evaluación en modo texto (todas)

Generado por `python -m evaluacion.evaluar` el 2026-10-15. 48 guiones de [datos/guiones/](../guiones/). Solo se analizan los turnos de quien llama, como en la llamada simulada.

| Estrategia | Detección | IC 95 % | Falsas alertas | IC 95 % | Precisión | Aviso (mediana) | Aviso (máx.) |
|---|---|---|---|---|---|---|---|
| por_fragmento | 19/24 (79 %) | 60–91 % | 1/24 (4 %) | 1–20 % | 95 % | 6,8 s | 11,2 s |
| acumulacion | 19/24 (79 %) | 60–91 % | 2/24 (8 %) | 2–26 % | 90 % | 6,8 s | 11,2 s |
| clasificador | 23/24 (96 %) | 80–99 % | 0/24 (0 %) | 0–14 % | 100 % | 6,4 s | 11,2 s |
| hibrida | 24/24 (100 %) | 86–100 % | 2/24 (8 %) | 2–26 % | 92 % | 6,4 s | 11,2 s |

## Errores

- **por_fragmento**: no detectadas r06, r09, r14, r15, r18; falsas alertas l13; alertas anticipadas 0.
- **acumulacion**: no detectadas r06, r09, r14, r15, r18; falsas alertas l06, l13; alertas anticipadas 0.
- **clasificador**: no detectadas g05; falsas alertas ninguna; alertas anticipadas 2.
- **hibrida**: no detectadas ninguna; falsas alertas l06, l13; alertas anticipadas 2.

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
| r13 | riesgo | suplanta_banco | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s |
| r14 | riesgo | familiar_falso | sin aviso | sin aviso | aviso en turno 2, 0,0 s | aviso en turno 2, 0,0 s |
| r15 | riesgo | soporte_falso | sin aviso | sin aviso | aviso en turno 1, 0,0 s | aviso en turno 1, 0,0 s |
| r16 | riesgo | premio_falso | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s |
| r17 | riesgo | extorsion | aviso en turno 1, 7,6 s | aviso en turno 1, 7,6 s | aviso en turno 1, 7,6 s | aviso en turno 1, 7,6 s |
| r18 | riesgo | suplanta_banco | sin aviso | sin aviso | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s |
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
| l13 | legitima | banco_real | aviso en turno 1 | aviso en turno 1 | sin aviso | aviso en turno 1 |
| l14 | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| l15 | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| l16 | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| l17 | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| l18 | legitima | vecinos | sin aviso | sin aviso | sin aviso | sin aviso |
| g01 | riesgo | suplanta_banco | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s |
| g02 | riesgo | familiar_falso | aviso en turno 3, 10,8 s | aviso en turno 3, 10,8 s | aviso en turno 3, 10,8 s | aviso en turno 3, 10,8 s |
| g03 | riesgo | extorsion | aviso en turno 1, 9,2 s | aviso en turno 1, 9,2 s | aviso en turno 1, 9,2 s | aviso en turno 1, 9,2 s |
| g04 | riesgo | soporte_falso | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| g05 | riesgo | premio_falso | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | sin aviso | aviso en turno 2, 9,2 s |
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
