# Evaluación en modo texto (todas)

Generado por `python -m evaluacion.evaluar` el 2026-11-14. 372 guiones de [datos/guiones/](../guiones/). Solo se analizan los turnos de quien llama, como en la llamada simulada.

| Estrategia | Detección | IC 95 % | Falsas alertas | IC 95 % | Precisión | F1 | Demora (mediana) | Demora (p95) | Tardías |
|---|---|---|---|---|---|---|---|---|---|
| por_fragmento | 114/186 (61 %) | 54–68 % | 1/186 (1 %) | 0–3 % | 99 % | 76 % | 0,0 s | 6,8 s | 9/114 |
| acumulacion | 177/186 (95 %) | 91–97 % | 29/186 (16 %) | 11–21 % | 86 % | 90 % | 0,0 s | 6,8 s | 18/177 |
| clasificador | 159/186 (85 %) | 80–90 % | 1/186 (1 %) | 0–3 % | 99 % | 92 % | 0,0 s | 0,0 s | 0/159 |
| hibrida | 186/186 (100 %) | 98–100 % | 29/186 (16 %) | 11–21 % | 87 % | 93 % | 0,0 s | 0,0 s | 0/186 |

## Comparación llamada a llamada

Diferencia = segunda estrategia menos primera, en puntos porcentuales. El intervalo sale de remuestrear 2000 veces familias completas de llamadas (una plantilla con todas sus regiones cuenta como una sola), porque comparten la forma del engaño. Si el intervalo incluye el cero, la diferencia no es concluyente con estos guiones.

**por_fragmento → acumulacion**

- Detección (42 familias de riesgo): +33,9 pp (IC 95 %: +13,9 a +53,2). Solo acumulacion: extorsion_vacuna (9 regiones), gradual_banco_cajero (9 regiones), gradual_dian_corresponsal (9 regiones), gradual_sobrino_clinica (9 regiones), gradual_paquete_premio (9 regiones), gradual_inversion_cupos (9 regiones), gradual_policia_estacion (9 regiones); solo por_fragmento: ninguna.
- Falsas alertas (42 familias legítimas): +15,1 pp (IC 95 %: +0,6 a +32,5). Solo acumulacion: l06, dificil_banco_bloqueo_real (9 regiones), dificil_dian_recordatorio (9 regiones), dificil_jefe_informe (9 regiones); solo por_fragmento: ninguna.
- Cuando ambas avisan: acumulacion avisa en un turno anterior en 0 llamadas y por_fragmento en 0.

**clasificador → hibrida**

- Detección (42 familias de riesgo): +14,5 pp (IC 95 %: +0,0 a +31,8). Solo hibrida: gradual_banco_cajero (9 regiones), gradual_paquete_premio (9 regiones), gradual_policia_estacion (9 regiones); solo clasificador: ninguna.
- Falsas alertas (42 familias legítimas): +15,1 pp (IC 95 %: +0,6 a +32,5). Solo hibrida: l06, dificil_banco_bloqueo_real (9 regiones), dificil_dian_recordatorio (9 regiones), dificil_jefe_informe (9 regiones); solo clasificador: ninguna.
- Cuando ambas avisan: hibrida avisa en un turno anterior en 0 llamadas y clasificador en 0.


## Errores

- **por_fragmento**: no detectadas r06, r09, r14, r15, r18, s-empleo_curso-valle-del-cauca, s-empleo_curso-santander, s-empleo_curso-tolima-y-huila, s-extorsion_vacuna-costa-caribe, s-extorsion_vacuna-antioquia, s-extorsion_vacuna-bogota, s-extorsion_vacuna-valle-del-cauca, s-extorsion_vacuna-santander, s-extorsion_vacuna-narino, s-extorsion_vacuna-llanos, s-extorsion_vacuna-tolima-y-huila, s-extorsion_vacuna-eje-cafetero, s-envio_aduana-valle-del-cauca, s-gradual_banco_cajero-costa-caribe, s-gradual_banco_cajero-antioquia, s-gradual_banco_cajero-bogota, s-gradual_banco_cajero-valle-del-cauca, s-gradual_banco_cajero-santander, s-gradual_banco_cajero-narino, s-gradual_banco_cajero-llanos, s-gradual_banco_cajero-tolima-y-huila, s-gradual_banco_cajero-eje-cafetero, s-gradual_dian_corresponsal-costa-caribe, s-gradual_dian_corresponsal-antioquia, s-gradual_dian_corresponsal-bogota, s-gradual_dian_corresponsal-valle-del-cauca, s-gradual_dian_corresponsal-santander, s-gradual_dian_corresponsal-narino, s-gradual_dian_corresponsal-llanos, s-gradual_dian_corresponsal-tolima-y-huila, s-gradual_dian_corresponsal-eje-cafetero, s-gradual_sobrino_clinica-costa-caribe, s-gradual_sobrino_clinica-antioquia, s-gradual_sobrino_clinica-bogota, s-gradual_sobrino_clinica-valle-del-cauca, s-gradual_sobrino_clinica-santander, s-gradual_sobrino_clinica-narino, s-gradual_sobrino_clinica-llanos, s-gradual_sobrino_clinica-tolima-y-huila, s-gradual_sobrino_clinica-eje-cafetero, s-gradual_paquete_premio-costa-caribe, s-gradual_paquete_premio-antioquia, s-gradual_paquete_premio-bogota, s-gradual_paquete_premio-valle-del-cauca, s-gradual_paquete_premio-santander, s-gradual_paquete_premio-narino, s-gradual_paquete_premio-llanos, s-gradual_paquete_premio-tolima-y-huila, s-gradual_paquete_premio-eje-cafetero, s-gradual_inversion_cupos-costa-caribe, s-gradual_inversion_cupos-antioquia, s-gradual_inversion_cupos-bogota, s-gradual_inversion_cupos-valle-del-cauca, s-gradual_inversion_cupos-santander, s-gradual_inversion_cupos-narino, s-gradual_inversion_cupos-llanos, s-gradual_inversion_cupos-tolima-y-huila, s-gradual_inversion_cupos-eje-cafetero, s-gradual_policia_estacion-costa-caribe, s-gradual_policia_estacion-antioquia, s-gradual_policia_estacion-bogota, s-gradual_policia_estacion-valle-del-cauca, s-gradual_policia_estacion-santander, s-gradual_policia_estacion-narino, s-gradual_policia_estacion-llanos, s-gradual_policia_estacion-tolima-y-huila, s-gradual_policia_estacion-eje-cafetero; falsas alertas l13; alertas anticipadas 0.
- **acumulacion**: no detectadas r06, r09, r14, r15, r18, s-empleo_curso-valle-del-cauca, s-empleo_curso-santander, s-empleo_curso-tolima-y-huila, s-envio_aduana-valle-del-cauca; falsas alertas l06, l13, s-dificil_banco_bloqueo_real-costa-caribe, s-dificil_banco_bloqueo_real-antioquia, s-dificil_banco_bloqueo_real-bogota, s-dificil_banco_bloqueo_real-valle-del-cauca, s-dificil_banco_bloqueo_real-santander, s-dificil_banco_bloqueo_real-narino, s-dificil_banco_bloqueo_real-llanos, s-dificil_banco_bloqueo_real-tolima-y-huila, s-dificil_banco_bloqueo_real-eje-cafetero, s-dificil_dian_recordatorio-costa-caribe, s-dificil_dian_recordatorio-antioquia, s-dificil_dian_recordatorio-bogota, s-dificil_dian_recordatorio-valle-del-cauca, s-dificil_dian_recordatorio-santander, s-dificil_dian_recordatorio-narino, s-dificil_dian_recordatorio-llanos, s-dificil_dian_recordatorio-tolima-y-huila, s-dificil_dian_recordatorio-eje-cafetero, s-dificil_jefe_informe-costa-caribe, s-dificil_jefe_informe-antioquia, s-dificil_jefe_informe-bogota, s-dificil_jefe_informe-valle-del-cauca, s-dificil_jefe_informe-santander, s-dificil_jefe_informe-narino, s-dificil_jefe_informe-llanos, s-dificil_jefe_informe-tolima-y-huila, s-dificil_jefe_informe-eje-cafetero; alertas anticipadas 0.
- **clasificador**: no detectadas s-gradual_banco_cajero-costa-caribe, s-gradual_banco_cajero-antioquia, s-gradual_banco_cajero-bogota, s-gradual_banco_cajero-valle-del-cauca, s-gradual_banco_cajero-santander, s-gradual_banco_cajero-narino, s-gradual_banco_cajero-llanos, s-gradual_banco_cajero-tolima-y-huila, s-gradual_banco_cajero-eje-cafetero, s-gradual_paquete_premio-costa-caribe, s-gradual_paquete_premio-antioquia, s-gradual_paquete_premio-bogota, s-gradual_paquete_premio-valle-del-cauca, s-gradual_paquete_premio-santander, s-gradual_paquete_premio-narino, s-gradual_paquete_premio-llanos, s-gradual_paquete_premio-tolima-y-huila, s-gradual_paquete_premio-eje-cafetero, s-gradual_policia_estacion-costa-caribe, s-gradual_policia_estacion-antioquia, s-gradual_policia_estacion-bogota, s-gradual_policia_estacion-valle-del-cauca, s-gradual_policia_estacion-santander, s-gradual_policia_estacion-narino, s-gradual_policia_estacion-llanos, s-gradual_policia_estacion-tolima-y-huila, s-gradual_policia_estacion-eje-cafetero; falsas alertas l13; alertas anticipadas 3.
- **hibrida**: no detectadas ninguna; falsas alertas l06, l13, s-dificil_banco_bloqueo_real-costa-caribe, s-dificil_banco_bloqueo_real-antioquia, s-dificil_banco_bloqueo_real-bogota, s-dificil_banco_bloqueo_real-valle-del-cauca, s-dificil_banco_bloqueo_real-santander, s-dificil_banco_bloqueo_real-narino, s-dificil_banco_bloqueo_real-llanos, s-dificil_banco_bloqueo_real-tolima-y-huila, s-dificil_banco_bloqueo_real-eje-cafetero, s-dificil_dian_recordatorio-costa-caribe, s-dificil_dian_recordatorio-antioquia, s-dificil_dian_recordatorio-bogota, s-dificil_dian_recordatorio-valle-del-cauca, s-dificil_dian_recordatorio-santander, s-dificil_dian_recordatorio-narino, s-dificil_dian_recordatorio-llanos, s-dificil_dian_recordatorio-tolima-y-huila, s-dificil_dian_recordatorio-eje-cafetero, s-dificil_jefe_informe-costa-caribe, s-dificil_jefe_informe-antioquia, s-dificil_jefe_informe-bogota, s-dificil_jefe_informe-valle-del-cauca, s-dificil_jefe_informe-santander, s-dificil_jefe_informe-narino, s-dificil_jefe_informe-llanos, s-dificil_jefe_informe-tolima-y-huila, s-dificil_jefe_informe-eje-cafetero; alertas anticipadas 3.

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
| r14 | riesgo | familiar_falso | sin aviso | sin aviso | aviso en turno 0, 0,0 s | aviso en turno 0, 0,0 s |
| r15 | riesgo | soporte_falso | sin aviso | sin aviso | aviso en turno 1, 0,0 s | aviso en turno 1, 0,0 s |
| r16 | riesgo | premio_falso | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 0, 0,0 s | aviso en turno 0, 0,0 s |
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
| l13 | legitima | banco_real | aviso en turno 1 | aviso en turno 1 | aviso en turno 1 | aviso en turno 1 |
| l14 | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| l15 | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| l16 | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| l17 | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| l18 | legitima | vecinos | sin aviso | sin aviso | sin aviso | sin aviso |
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
| s-suplanta_banco_codigo-costa-caribe | riesgo | suplanta_banco | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s |
| s-suplanta_banco_codigo-antioquia | riesgo | suplanta_banco | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-suplanta_banco_codigo-bogota | riesgo | suplanta_banco | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-suplanta_banco_codigo-valle-del-cauca | riesgo | suplanta_banco | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s |
| s-suplanta_banco_codigo-santander | riesgo | suplanta_banco | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-suplanta_banco_codigo-narino | riesgo | suplanta_banco | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-suplanta_banco_codigo-llanos | riesgo | suplanta_banco | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-suplanta_banco_codigo-tolima-y-huila | riesgo | suplanta_banco | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| s-suplanta_banco_codigo-eje-cafetero | riesgo | suplanta_banco | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-familiar_numero_nuevo-costa-caribe | riesgo | familiar_falso | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s |
| s-familiar_numero_nuevo-antioquia | riesgo | familiar_falso | aviso en turno 4, 7,2 s | aviso en turno 4, 7,2 s | aviso en turno 4, 7,2 s | aviso en turno 4, 7,2 s |
| s-familiar_numero_nuevo-bogota | riesgo | familiar_falso | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s |
| s-familiar_numero_nuevo-valle-del-cauca | riesgo | familiar_falso | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s |
| s-familiar_numero_nuevo-santander | riesgo | familiar_falso | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s |
| s-familiar_numero_nuevo-narino | riesgo | familiar_falso | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s |
| s-familiar_numero_nuevo-llanos | riesgo | familiar_falso | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s |
| s-familiar_numero_nuevo-tolima-y-huila | riesgo | familiar_falso | aviso en turno 4, 7,2 s | aviso en turno 4, 7,2 s | aviso en turno 4, 7,2 s | aviso en turno 4, 7,2 s |
| s-familiar_numero_nuevo-eje-cafetero | riesgo | familiar_falso | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s | aviso en turno 4, 6,8 s |
| s-premio_envio-costa-caribe | riesgo | premio_falso | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| s-premio_envio-antioquia | riesgo | premio_falso | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s |
| s-premio_envio-bogota | riesgo | premio_falso | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-premio_envio-valle-del-cauca | riesgo | premio_falso | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| s-premio_envio-santander | riesgo | premio_falso | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-premio_envio-narino | riesgo | premio_falso | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-premio_envio-llanos | riesgo | premio_falso | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s |
| s-premio_envio-tolima-y-huila | riesgo | premio_falso | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-premio_envio-eje-cafetero | riesgo | premio_falso | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s |
| s-entidad_embargo-costa-caribe | riesgo | suplanta_entidad | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s |
| s-entidad_embargo-antioquia | riesgo | suplanta_entidad | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s |
| s-entidad_embargo-bogota | riesgo | suplanta_entidad | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s |
| s-entidad_embargo-valle-del-cauca | riesgo | suplanta_entidad | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s |
| s-entidad_embargo-santander | riesgo | suplanta_entidad | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s |
| s-entidad_embargo-narino | riesgo | suplanta_entidad | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s | aviso en turno 3, 6,8 s |
| s-entidad_embargo-llanos | riesgo | suplanta_entidad | aviso en turno 3, 7,2 s | aviso en turno 3, 7,2 s | aviso en turno 3, 7,2 s | aviso en turno 3, 7,2 s |
| s-entidad_embargo-tolima-y-huila | riesgo | suplanta_entidad | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s |
| s-entidad_embargo-eje-cafetero | riesgo | suplanta_entidad | aviso en turno 3, 7,2 s | aviso en turno 3, 7,2 s | aviso en turno 3, 7,2 s | aviso en turno 3, 7,2 s |
| s-inversion_doble-costa-caribe | riesgo | inversion_falsa | aviso en turno 4, 14,0 s | aviso en turno 4, 14,0 s | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s |
| s-inversion_doble-antioquia | riesgo | inversion_falsa | aviso en turno 4, 14,8 s | aviso en turno 4, 14,8 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| s-inversion_doble-bogota | riesgo | inversion_falsa | aviso en turno 4, 14,8 s | aviso en turno 4, 14,8 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| s-inversion_doble-valle-del-cauca | riesgo | inversion_falsa | aviso en turno 4, 14,0 s | aviso en turno 4, 14,0 s | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s |
| s-inversion_doble-santander | riesgo | inversion_falsa | aviso en turno 4, 14,4 s | aviso en turno 4, 14,4 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| s-inversion_doble-narino | riesgo | inversion_falsa | aviso en turno 4, 14,4 s | aviso en turno 4, 14,4 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| s-inversion_doble-llanos | riesgo | inversion_falsa | aviso en turno 4, 14,0 s | aviso en turno 4, 14,0 s | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s |
| s-inversion_doble-tolima-y-huila | riesgo | inversion_falsa | aviso en turno 4, 14,4 s | aviso en turno 4, 14,4 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| s-inversion_doble-eje-cafetero | riesgo | inversion_falsa | aviso en turno 4, 14,4 s | aviso en turno 4, 14,4 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| s-empleo_curso-costa-caribe | riesgo | empleo_falso | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| s-empleo_curso-antioquia | riesgo | empleo_falso | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s |
| s-empleo_curso-bogota | riesgo | empleo_falso | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-empleo_curso-valle-del-cauca | riesgo | empleo_falso | sin aviso | sin aviso | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s |
| s-empleo_curso-santander | riesgo | empleo_falso | sin aviso | sin aviso | aviso en turno 2, 8,0 s | aviso en turno 2, 8,0 s |
| s-empleo_curso-narino | riesgo | empleo_falso | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s |
| s-empleo_curso-llanos | riesgo | empleo_falso | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s | aviso en turno 2, 7,2 s |
| s-empleo_curso-tolima-y-huila | riesgo | empleo_falso | sin aviso | sin aviso | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-empleo_curso-eje-cafetero | riesgo | empleo_falso | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s | aviso en turno 2, 7,6 s |
| s-extorsion_vacuna-costa-caribe | riesgo | extorsion | sin aviso | aviso en turno 5, 12,8 s | aviso en turno 3, 5,6 s | aviso en turno 3, 5,6 s |
| s-extorsion_vacuna-antioquia | riesgo | extorsion | sin aviso | aviso en turno 5, 12,4 s | aviso en turno 3, 5,6 s | aviso en turno 3, 5,6 s |
| s-extorsion_vacuna-bogota | riesgo | extorsion | sin aviso | aviso en turno 5, 13,2 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-extorsion_vacuna-valle-del-cauca | riesgo | extorsion | sin aviso | aviso en turno 5, 12,8 s | aviso en turno 3, 5,6 s | aviso en turno 3, 5,6 s |
| s-extorsion_vacuna-santander | riesgo | extorsion | sin aviso | aviso en turno 5, 12,8 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-extorsion_vacuna-narino | riesgo | extorsion | sin aviso | aviso en turno 5, 12,8 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-extorsion_vacuna-llanos | riesgo | extorsion | sin aviso | aviso en turno 5, 12,4 s | aviso en turno 3, 5,6 s | aviso en turno 3, 5,6 s |
| s-extorsion_vacuna-tolima-y-huila | riesgo | extorsion | sin aviso | aviso en turno 5, 12,4 s | aviso en turno 3, 5,6 s | aviso en turno 3, 5,6 s |
| s-extorsion_vacuna-eje-cafetero | riesgo | extorsion | sin aviso | aviso en turno 5, 12,4 s | aviso en turno 3, 5,6 s | aviso en turno 3, 5,6 s |
| s-suplanta_banco_clave-costa-caribe | riesgo | suplanta_banco | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| s-suplanta_banco_clave-antioquia | riesgo | suplanta_banco | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s |
| s-suplanta_banco_clave-bogota | riesgo | suplanta_banco | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| s-suplanta_banco_clave-valle-del-cauca | riesgo | suplanta_banco | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| s-suplanta_banco_clave-santander | riesgo | suplanta_banco | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s |
| s-suplanta_banco_clave-narino | riesgo | suplanta_banco | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s |
| s-suplanta_banco_clave-llanos | riesgo | suplanta_banco | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s |
| s-suplanta_banco_clave-tolima-y-huila | riesgo | suplanta_banco | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| s-suplanta_banco_clave-eje-cafetero | riesgo | suplanta_banco | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| s-familiar_detenido-costa-caribe | riesgo | familiar_falso | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-familiar_detenido-antioquia | riesgo | familiar_falso | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-familiar_detenido-bogota | riesgo | familiar_falso | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s | aviso en turno 3, 7,6 s |
| s-familiar_detenido-valle-del-cauca | riesgo | familiar_falso | aviso en turno 3, 5,6 s | aviso en turno 3, 5,6 s | aviso en turno 3, 5,6 s | aviso en turno 3, 5,6 s |
| s-familiar_detenido-santander | riesgo | familiar_falso | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s |
| s-familiar_detenido-narino | riesgo | familiar_falso | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s |
| s-familiar_detenido-llanos | riesgo | familiar_falso | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-familiar_detenido-tolima-y-huila | riesgo | familiar_falso | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s |
| s-familiar_detenido-eje-cafetero | riesgo | familiar_falso | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-soporte_aplicacion-costa-caribe | riesgo | soporte_falso | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| s-soporte_aplicacion-antioquia | riesgo | soporte_falso | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s |
| s-soporte_aplicacion-bogota | riesgo | soporte_falso | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| s-soporte_aplicacion-valle-del-cauca | riesgo | soporte_falso | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| s-soporte_aplicacion-santander | riesgo | soporte_falso | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s | aviso en turno 2, 9,2 s |
| s-soporte_aplicacion-narino | riesgo | soporte_falso | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s |
| s-soporte_aplicacion-llanos | riesgo | soporte_falso | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s |
| s-soporte_aplicacion-tolima-y-huila | riesgo | soporte_falso | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s |
| s-soporte_aplicacion-eje-cafetero | riesgo | soporte_falso | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s | aviso en turno 2, 8,8 s |
| s-extorsion_familia-costa-caribe | riesgo | extorsion | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s |
| s-extorsion_familia-antioquia | riesgo | extorsion | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-extorsion_familia-bogota | riesgo | extorsion | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-extorsion_familia-valle-del-cauca | riesgo | extorsion | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-extorsion_familia-santander | riesgo | extorsion | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s | aviso en turno 3, 6,4 s |
| s-extorsion_familia-narino | riesgo | extorsion | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-extorsion_familia-llanos | riesgo | extorsion | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-extorsion_familia-tolima-y-huila | riesgo | extorsion | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-extorsion_familia-eje-cafetero | riesgo | extorsion | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s | aviso en turno 3, 6,0 s |
| s-envio_aduana-costa-caribe | riesgo | envio_falso | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s |
| s-envio_aduana-antioquia | riesgo | envio_falso | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s |
| s-envio_aduana-bogota | riesgo | envio_falso | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s | aviso en turno 2, 8,4 s |
| s-envio_aduana-valle-del-cauca | riesgo | envio_falso | sin aviso | sin aviso | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s |
| s-envio_aduana-santander | riesgo | envio_falso | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s | aviso en turno 2, 6,0 s |
| s-envio_aduana-narino | riesgo | envio_falso | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s |
| s-envio_aduana-llanos | riesgo | envio_falso | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s |
| s-envio_aduana-tolima-y-huila | riesgo | envio_falso | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s | aviso en turno 2, 5,6 s |
| s-envio_aduana-eje-cafetero | riesgo | envio_falso | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s | aviso en turno 2, 6,4 s |
| s-banco_confirma_compra-costa-caribe | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_confirma_compra-antioquia | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_confirma_compra-bogota | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_confirma_compra-valle-del-cauca | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_confirma_compra-santander | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_confirma_compra-narino | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_confirma_compra-llanos | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_confirma_compra-tolima-y-huila | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_confirma_compra-eje-cafetero | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_mercado-costa-caribe | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_mercado-antioquia | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_mercado-bogota | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_mercado-valle-del-cauca | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_mercado-santander | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_mercado-narino | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_mercado-llanos | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_mercado-tolima-y-huila | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_mercado-eje-cafetero | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-domicilio_efectivo-costa-caribe | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-domicilio_efectivo-antioquia | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-domicilio_efectivo-bogota | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-domicilio_efectivo-valle-del-cauca | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-domicilio_efectivo-santander | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-domicilio_efectivo-narino | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-domicilio_efectivo-llanos | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-domicilio_efectivo-tolima-y-huila | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-domicilio_efectivo-eje-cafetero | legitima | domicilio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-eps_cita-costa-caribe | legitima | cita_medica | sin aviso | sin aviso | sin aviso | sin aviso |
| s-eps_cita-antioquia | legitima | cita_medica | sin aviso | sin aviso | sin aviso | sin aviso |
| s-eps_cita-bogota | legitima | cita_medica | sin aviso | sin aviso | sin aviso | sin aviso |
| s-eps_cita-valle-del-cauca | legitima | cita_medica | sin aviso | sin aviso | sin aviso | sin aviso |
| s-eps_cita-santander | legitima | cita_medica | sin aviso | sin aviso | sin aviso | sin aviso |
| s-eps_cita-narino | legitima | cita_medica | sin aviso | sin aviso | sin aviso | sin aviso |
| s-eps_cita-llanos | legitima | cita_medica | sin aviso | sin aviso | sin aviso | sin aviso |
| s-eps_cita-tolima-y-huila | legitima | cita_medica | sin aviso | sin aviso | sin aviso | sin aviso |
| s-eps_cita-eje-cafetero | legitima | cita_medica | sin aviso | sin aviso | sin aviso | sin aviso |
| s-trabajo_obra-costa-caribe | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| s-trabajo_obra-antioquia | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| s-trabajo_obra-bogota | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| s-trabajo_obra-valle-del-cauca | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| s-trabajo_obra-santander | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| s-trabajo_obra-narino | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| s-trabajo_obra-llanos | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| s-trabajo_obra-tolima-y-huila | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| s-trabajo_obra-eje-cafetero | legitima | trabajo | sin aviso | sin aviso | sin aviso | sin aviso |
| s-amigos_asado-costa-caribe | legitima | amistad | sin aviso | sin aviso | sin aviso | sin aviso |
| s-amigos_asado-antioquia | legitima | amistad | sin aviso | sin aviso | sin aviso | sin aviso |
| s-amigos_asado-bogota | legitima | amistad | sin aviso | sin aviso | sin aviso | sin aviso |
| s-amigos_asado-valle-del-cauca | legitima | amistad | sin aviso | sin aviso | sin aviso | sin aviso |
| s-amigos_asado-santander | legitima | amistad | sin aviso | sin aviso | sin aviso | sin aviso |
| s-amigos_asado-narino | legitima | amistad | sin aviso | sin aviso | sin aviso | sin aviso |
| s-amigos_asado-llanos | legitima | amistad | sin aviso | sin aviso | sin aviso | sin aviso |
| s-amigos_asado-tolima-y-huila | legitima | amistad | sin aviso | sin aviso | sin aviso | sin aviso |
| s-amigos_asado-eje-cafetero | legitima | amistad | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_tarjeta_lista-costa-caribe | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_tarjeta_lista-antioquia | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_tarjeta_lista-bogota | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_tarjeta_lista-valle-del-cauca | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_tarjeta_lista-santander | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_tarjeta_lista-narino | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_tarjeta_lista-llanos | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_tarjeta_lista-tolima-y-huila | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-banco_tarjeta_lista-eje-cafetero | legitima | banco_real | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_enferma-costa-caribe | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_enferma-antioquia | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_enferma-bogota | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_enferma-valle-del-cauca | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_enferma-santander | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_enferma-narino | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_enferma-llanos | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_enferma-tolima-y-huila | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-familia_enferma-eje-cafetero | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-energia_corte-costa-caribe | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| s-energia_corte-antioquia | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| s-energia_corte-bogota | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| s-energia_corte-valle-del-cauca | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| s-energia_corte-santander | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| s-energia_corte-narino | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| s-energia_corte-llanos | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| s-energia_corte-tolima-y-huila | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| s-energia_corte-eje-cafetero | legitima | servicios | sin aviso | sin aviso | sin aviso | sin aviso |
| s-encuesta_barrio-costa-caribe | legitima | encuesta | sin aviso | sin aviso | sin aviso | sin aviso |
| s-encuesta_barrio-antioquia | legitima | encuesta | sin aviso | sin aviso | sin aviso | sin aviso |
| s-encuesta_barrio-bogota | legitima | encuesta | sin aviso | sin aviso | sin aviso | sin aviso |
| s-encuesta_barrio-valle-del-cauca | legitima | encuesta | sin aviso | sin aviso | sin aviso | sin aviso |
| s-encuesta_barrio-santander | legitima | encuesta | sin aviso | sin aviso | sin aviso | sin aviso |
| s-encuesta_barrio-narino | legitima | encuesta | sin aviso | sin aviso | sin aviso | sin aviso |
| s-encuesta_barrio-llanos | legitima | encuesta | sin aviso | sin aviso | sin aviso | sin aviso |
| s-encuesta_barrio-tolima-y-huila | legitima | encuesta | sin aviso | sin aviso | sin aviso | sin aviso |
| s-encuesta_barrio-eje-cafetero | legitima | encuesta | sin aviso | sin aviso | sin aviso | sin aviso |
| s-colegio_reunion-costa-caribe | legitima | colegio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-colegio_reunion-antioquia | legitima | colegio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-colegio_reunion-bogota | legitima | colegio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-colegio_reunion-valle-del-cauca | legitima | colegio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-colegio_reunion-santander | legitima | colegio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-colegio_reunion-narino | legitima | colegio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-colegio_reunion-llanos | legitima | colegio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-colegio_reunion-tolima-y-huila | legitima | colegio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-colegio_reunion-eje-cafetero | legitima | colegio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-tienda_contra_entrega-costa-caribe | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-tienda_contra_entrega-antioquia | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-tienda_contra_entrega-bogota | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-tienda_contra_entrega-valle-del-cauca | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-tienda_contra_entrega-santander | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-tienda_contra_entrega-narino | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-tienda_contra_entrega-llanos | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-tienda_contra_entrega-tolima-y-huila | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-tienda_contra_entrega-eje-cafetero | legitima | comercio | sin aviso | sin aviso | sin aviso | sin aviso |
| s-gradual_banco_cajero-costa-caribe | riesgo | suplanta_banco | sin aviso | aviso en turno 4, 7,6 s | sin aviso | aviso en turno 4, 7,6 s |
| s-gradual_banco_cajero-antioquia | riesgo | suplanta_banco | sin aviso | aviso en turno 4, 7,2 s | sin aviso | aviso en turno 4, 7,2 s |
| s-gradual_banco_cajero-bogota | riesgo | suplanta_banco | sin aviso | aviso en turno 4, 7,6 s | sin aviso | aviso en turno 4, 7,6 s |
| s-gradual_banco_cajero-valle-del-cauca | riesgo | suplanta_banco | sin aviso | aviso en turno 4, 7,6 s | sin aviso | aviso en turno 4, 7,6 s |
| s-gradual_banco_cajero-santander | riesgo | suplanta_banco | sin aviso | aviso en turno 4, 7,6 s | sin aviso | aviso en turno 4, 7,6 s |
| s-gradual_banco_cajero-narino | riesgo | suplanta_banco | sin aviso | aviso en turno 4, 7,2 s | sin aviso | aviso en turno 4, 7,2 s |
| s-gradual_banco_cajero-llanos | riesgo | suplanta_banco | sin aviso | aviso en turno 4, 7,2 s | sin aviso | aviso en turno 4, 7,2 s |
| s-gradual_banco_cajero-tolima-y-huila | riesgo | suplanta_banco | sin aviso | aviso en turno 4, 7,2 s | sin aviso | aviso en turno 4, 7,2 s |
| s-gradual_banco_cajero-eje-cafetero | riesgo | suplanta_banco | sin aviso | aviso en turno 4, 7,2 s | sin aviso | aviso en turno 4, 7,2 s |
| s-gradual_dian_corresponsal-costa-caribe | riesgo | suplanta_entidad | sin aviso | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s |
| s-gradual_dian_corresponsal-antioquia | riesgo | suplanta_entidad | sin aviso | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s |
| s-gradual_dian_corresponsal-bogota | riesgo | suplanta_entidad | sin aviso | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s |
| s-gradual_dian_corresponsal-valle-del-cauca | riesgo | suplanta_entidad | sin aviso | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s |
| s-gradual_dian_corresponsal-santander | riesgo | suplanta_entidad | sin aviso | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s |
| s-gradual_dian_corresponsal-narino | riesgo | suplanta_entidad | sin aviso | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s |
| s-gradual_dian_corresponsal-llanos | riesgo | suplanta_entidad | sin aviso | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s |
| s-gradual_dian_corresponsal-tolima-y-huila | riesgo | suplanta_entidad | sin aviso | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s |
| s-gradual_dian_corresponsal-eje-cafetero | riesgo | suplanta_entidad | sin aviso | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s | aviso en turno 4, 7,6 s |
| s-gradual_sobrino_clinica-costa-caribe | riesgo | familiar_falso | sin aviso | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s |
| s-gradual_sobrino_clinica-antioquia | riesgo | familiar_falso | sin aviso | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s |
| s-gradual_sobrino_clinica-bogota | riesgo | familiar_falso | sin aviso | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s |
| s-gradual_sobrino_clinica-valle-del-cauca | riesgo | familiar_falso | sin aviso | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s |
| s-gradual_sobrino_clinica-santander | riesgo | familiar_falso | sin aviso | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s |
| s-gradual_sobrino_clinica-narino | riesgo | familiar_falso | sin aviso | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s |
| s-gradual_sobrino_clinica-llanos | riesgo | familiar_falso | sin aviso | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s |
| s-gradual_sobrino_clinica-tolima-y-huila | riesgo | familiar_falso | sin aviso | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s |
| s-gradual_sobrino_clinica-eje-cafetero | riesgo | familiar_falso | sin aviso | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s | aviso en turno 6, 6,4 s |
| s-gradual_paquete_premio-costa-caribe | riesgo | premio_falso | sin aviso | aviso en turno 4, 8,0 s | sin aviso | aviso en turno 4, 8,0 s |
| s-gradual_paquete_premio-antioquia | riesgo | premio_falso | sin aviso | aviso en turno 4, 8,0 s | sin aviso | aviso en turno 4, 8,0 s |
| s-gradual_paquete_premio-bogota | riesgo | premio_falso | sin aviso | aviso en turno 4, 8,0 s | sin aviso | aviso en turno 4, 8,0 s |
| s-gradual_paquete_premio-valle-del-cauca | riesgo | premio_falso | sin aviso | aviso en turno 4, 8,0 s | sin aviso | aviso en turno 4, 8,0 s |
| s-gradual_paquete_premio-santander | riesgo | premio_falso | sin aviso | aviso en turno 4, 8,0 s | sin aviso | aviso en turno 4, 8,0 s |
| s-gradual_paquete_premio-narino | riesgo | premio_falso | sin aviso | aviso en turno 4, 8,0 s | sin aviso | aviso en turno 4, 8,0 s |
| s-gradual_paquete_premio-llanos | riesgo | premio_falso | sin aviso | aviso en turno 4, 8,0 s | sin aviso | aviso en turno 4, 8,0 s |
| s-gradual_paquete_premio-tolima-y-huila | riesgo | premio_falso | sin aviso | aviso en turno 4, 8,0 s | sin aviso | aviso en turno 4, 8,0 s |
| s-gradual_paquete_premio-eje-cafetero | riesgo | premio_falso | sin aviso | aviso en turno 4, 8,0 s | sin aviso | aviso en turno 4, 8,0 s |
| s-gradual_inversion_cupos-costa-caribe | riesgo | inversion_falsa | sin aviso | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s |
| s-gradual_inversion_cupos-antioquia | riesgo | inversion_falsa | sin aviso | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s |
| s-gradual_inversion_cupos-bogota | riesgo | inversion_falsa | sin aviso | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s |
| s-gradual_inversion_cupos-valle-del-cauca | riesgo | inversion_falsa | sin aviso | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s |
| s-gradual_inversion_cupos-santander | riesgo | inversion_falsa | sin aviso | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s |
| s-gradual_inversion_cupos-narino | riesgo | inversion_falsa | sin aviso | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s |
| s-gradual_inversion_cupos-llanos | riesgo | inversion_falsa | sin aviso | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s |
| s-gradual_inversion_cupos-tolima-y-huila | riesgo | inversion_falsa | sin aviso | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s |
| s-gradual_inversion_cupos-eje-cafetero | riesgo | inversion_falsa | sin aviso | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s | aviso en turno 4, 6,4 s |
| s-gradual_policia_estacion-costa-caribe | riesgo | extorsion | sin aviso | aviso en turno 4, 6,4 s | sin aviso | aviso en turno 4, 6,4 s |
| s-gradual_policia_estacion-antioquia | riesgo | extorsion | sin aviso | aviso en turno 4, 6,4 s | sin aviso | aviso en turno 4, 6,4 s |
| s-gradual_policia_estacion-bogota | riesgo | extorsion | sin aviso | aviso en turno 4, 6,4 s | sin aviso | aviso en turno 4, 6,4 s |
| s-gradual_policia_estacion-valle-del-cauca | riesgo | extorsion | sin aviso | aviso en turno 4, 6,4 s | sin aviso | aviso en turno 4, 6,4 s |
| s-gradual_policia_estacion-santander | riesgo | extorsion | sin aviso | aviso en turno 4, 6,4 s | sin aviso | aviso en turno 4, 6,4 s |
| s-gradual_policia_estacion-narino | riesgo | extorsion | sin aviso | aviso en turno 4, 6,4 s | sin aviso | aviso en turno 4, 6,4 s |
| s-gradual_policia_estacion-llanos | riesgo | extorsion | sin aviso | aviso en turno 4, 6,4 s | sin aviso | aviso en turno 4, 6,4 s |
| s-gradual_policia_estacion-tolima-y-huila | riesgo | extorsion | sin aviso | aviso en turno 4, 6,4 s | sin aviso | aviso en turno 4, 6,4 s |
| s-gradual_policia_estacion-eje-cafetero | riesgo | extorsion | sin aviso | aviso en turno 4, 6,4 s | sin aviso | aviso en turno 4, 6,4 s |
| s-dificil_banco_bloqueo_real-costa-caribe | legitima | banco | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_banco_bloqueo_real-antioquia | legitima | banco | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_banco_bloqueo_real-bogota | legitima | banco | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_banco_bloqueo_real-valle-del-cauca | legitima | banco | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_banco_bloqueo_real-santander | legitima | banco | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_banco_bloqueo_real-narino | legitima | banco | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_banco_bloqueo_real-llanos | legitima | banco | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_banco_bloqueo_real-tolima-y-huila | legitima | banco | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_banco_bloqueo_real-eje-cafetero | legitima | banco | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_dian_recordatorio-costa-caribe | legitima | entidad | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_dian_recordatorio-antioquia | legitima | entidad | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_dian_recordatorio-bogota | legitima | entidad | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_dian_recordatorio-valle-del-cauca | legitima | entidad | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_dian_recordatorio-santander | legitima | entidad | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_dian_recordatorio-narino | legitima | entidad | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_dian_recordatorio-llanos | legitima | entidad | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_dian_recordatorio-tolima-y-huila | legitima | entidad | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_dian_recordatorio-eje-cafetero | legitima | entidad | sin aviso | aviso en turno 4 | sin aviso | aviso en turno 4 |
| s-dificil_jefe_informe-costa-caribe | legitima | trabajo | sin aviso | aviso en turno 6 | sin aviso | aviso en turno 6 |
| s-dificil_jefe_informe-antioquia | legitima | trabajo | sin aviso | aviso en turno 6 | sin aviso | aviso en turno 6 |
| s-dificil_jefe_informe-bogota | legitima | trabajo | sin aviso | aviso en turno 6 | sin aviso | aviso en turno 6 |
| s-dificil_jefe_informe-valle-del-cauca | legitima | trabajo | sin aviso | aviso en turno 6 | sin aviso | aviso en turno 6 |
| s-dificil_jefe_informe-santander | legitima | trabajo | sin aviso | aviso en turno 6 | sin aviso | aviso en turno 6 |
| s-dificil_jefe_informe-narino | legitima | trabajo | sin aviso | aviso en turno 6 | sin aviso | aviso en turno 6 |
| s-dificil_jefe_informe-llanos | legitima | trabajo | sin aviso | aviso en turno 6 | sin aviso | aviso en turno 6 |
| s-dificil_jefe_informe-tolima-y-huila | legitima | trabajo | sin aviso | aviso en turno 6 | sin aviso | aviso en turno 6 |
| s-dificil_jefe_informe-eje-cafetero | legitima | trabajo | sin aviso | aviso en turno 6 | sin aviso | aviso en turno 6 |
| s-dificil_papa_varado-costa-caribe | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_papa_varado-antioquia | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_papa_varado-bogota | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_papa_varado-valle-del-cauca | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_papa_varado-santander | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_papa_varado-narino | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_papa_varado-llanos | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_papa_varado-tolima-y-huila | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_papa_varado-eje-cafetero | legitima | familia | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_operador_regalo-costa-caribe | legitima | operador | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_operador_regalo-antioquia | legitima | operador | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_operador_regalo-bogota | legitima | operador | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_operador_regalo-valle-del-cauca | legitima | operador | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_operador_regalo-santander | legitima | operador | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_operador_regalo-narino | legitima | operador | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_operador_regalo-llanos | legitima | operador | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_operador_regalo-tolima-y-huila | legitima | operador | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_operador_regalo-eje-cafetero | legitima | operador | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_clinica_accidente-costa-caribe | legitima | salud | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_clinica_accidente-antioquia | legitima | salud | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_clinica_accidente-bogota | legitima | salud | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_clinica_accidente-valle-del-cauca | legitima | salud | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_clinica_accidente-santander | legitima | salud | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_clinica_accidente-narino | legitima | salud | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_clinica_accidente-llanos | legitima | salud | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_clinica_accidente-tolima-y-huila | legitima | salud | sin aviso | sin aviso | sin aviso | sin aviso |
| s-dificil_clinica_accidente-eje-cafetero | legitima | salud | sin aviso | sin aviso | sin aviso | sin aviso |

## Cómo leerlo

- La demora va desde que termina la primera petición riesgosa hasta el aviso. Es negativa si el aviso llega antes; es tardía si pasa de 5,0 s, valor fijado antes de probar. La mediana y el percentil 95 solo cuentan las llamadas detectadas; las no detectadas se listan aparte.
- Los tiempos de la tabla por guion se miden desde que empieza el turno con la solicitud de riesgo hasta que termina el turno que dispara el aviso; en modo texto, la duración de cada turno se estima a 2,5 palabras por segundo.
- Una alerta anticipada ocurre antes del turno anotado como solicitud de riesgo.
- Con tan pocos guiones los intervalos de confianza son anchos: sirven para comparar estrategias, no como cifra definitiva.
- Los guiones los escribió el mismo equipo que escribió las reglas; por eso la partición reservada se usa solo para el informe final.
