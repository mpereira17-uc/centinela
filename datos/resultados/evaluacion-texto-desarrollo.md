# Evaluación en modo texto (desarrollo)

Generado por `python -m evaluacion.evaluar` el 2026-10-14. 24 guiones de [datos/guiones/guiones.json](../guiones/guiones.json). Solo se analizan los turnos de quien llama, como en la llamada simulada.

| Estrategia | Detección | IC 95 % | Falsas alertas | IC 95 % | Precisión | Aviso (mediana) | Aviso (máx.) |
|---|---|---|---|---|---|---|---|
| por_fragmento | 10/12 (83 %) | 55–95 % | 0/12 (0 %) | 0–24 % | 100 % | 6,4 s | 7,6 s |
| acumulacion | 10/12 (83 %) | 55–95 % | 1/12 (8 %) | 1–35 % | 91 % | 6,4 s | 7,6 s |

## Errores

- **por_fragmento**: no detectadas r06, r09; falsas alertas ninguna; alertas anticipadas 0.
- **acumulacion**: no detectadas r06, r09; falsas alertas l06; alertas anticipadas 0.

## Por guion

| Guion | Etiqueta | Categoría | por_fragmento | acumulacion |
|---|---|---|---|---|
| r01 | riesgo | suplanta_banco | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s |
| r02 | riesgo | suplanta_banco | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| r03 | riesgo | familiar_falso | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s |
| r04 | riesgo | soporte_falso | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s |
| r05 | riesgo | premio_falso | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s |
| r06 | riesgo | extorsion | sin aviso | sin aviso |
| r07 | riesgo | suplanta_entidad | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s |
| r08 | riesgo | inversion_falsa | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s |
| r09 | riesgo | suplanta_banco | sin aviso | sin aviso |
| r10 | riesgo | envio_falso | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s |
| r11 | riesgo | empleo_falso | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s |
| r12 | riesgo | suplanta_entidad | aviso en turno 2, 5,2 s | aviso en turno 2, 5,2 s |
| l01 | legitima | banco_real | sin aviso | sin aviso |
| l02 | legitima | cita_medica | sin aviso | sin aviso |
| l03 | legitima | domicilio | sin aviso | sin aviso |
| l04 | legitima | familia | sin aviso | sin aviso |
| l05 | legitima | telefonia | sin aviso | sin aviso |
| l06 | legitima | banco_real | sin aviso | aviso en turno 3 |
| l07 | legitima | trabajo | sin aviso | sin aviso |
| l08 | legitima | encuesta | sin aviso | sin aviso |
| l09 | legitima | colegio | sin aviso | sin aviso |
| l10 | legitima | domicilio | sin aviso | sin aviso |
| l11 | legitima | amistad | sin aviso | sin aviso |
| l12 | legitima | salud | sin aviso | sin aviso |

## Cómo leerlo

- Los tiempos se miden desde que empieza el turno con la solicitud de riesgo hasta que termina el turno que dispara el aviso; en modo texto, la duración de cada turno se estima a 2,5 palabras por segundo.
- Una alerta anticipada ocurre antes del turno anotado como solicitud de riesgo.
- Con tan pocos guiones los intervalos de confianza son anchos: sirven para comparar estrategias, no como cifra definitiva.
- Los guiones los escribió el mismo equipo que escribió las reglas; por eso la partición reservada se usa solo para el informe final.
