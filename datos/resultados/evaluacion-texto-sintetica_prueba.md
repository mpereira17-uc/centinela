# Evaluación en modo texto (sintetica_prueba)

Generado por `python -m evaluacion.evaluar` el 2026-10-15. 90 guiones de [datos/guiones/guiones-sinteticos.json](../guiones/guiones-sinteticos.json). Solo se analizan los turnos de quien llama, como en la llamada simulada.

| Estrategia | Detección | IC 95 % | Falsas alertas | IC 95 % | Precisión | Aviso (mediana) | Aviso (máx.) |
|---|---|---|---|---|---|---|---|
| por_fragmento | 44/45 (98 %) | 88–100 % | 0/45 (0 %) | 0–8 % | 100 % | 6,4 s | 9,2 s |
| acumulacion | 44/45 (98 %) | 88–100 % | 0/45 (0 %) | 0–8 % | 100 % | 6,4 s | 9,2 s |
| clasificador | 45/45 (100 %) | 92–100 % | 0/45 (0 %) | 0–8 % | 100 % | 6,4 s | 9,2 s |
| hibrida | 45/45 (100 %) | 92–100 % | 0/45 (0 %) | 0–8 % | 100 % | 6,4 s | 9,2 s |

## Errores

- **por_fragmento**: no detectadas s-envio_aduana-valle-del-cauca; falsas alertas ninguna; alertas anticipadas 0.
- **acumulacion**: no detectadas s-envio_aduana-valle-del-cauca; falsas alertas ninguna; alertas anticipadas 0.
- **clasificador**: no detectadas ninguna; falsas alertas ninguna; alertas anticipadas 0.
- **hibrida**: no detectadas ninguna; falsas alertas ninguna; alertas anticipadas 0.

## Por guion

| Guion | Etiqueta | Categoría | por_fragmento | acumulacion | clasificador | hibrida |
|---|---|---|---|---|---|---|
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

## Cómo leerlo

- Los tiempos se miden desde que empieza el turno con la solicitud de riesgo hasta que termina el turno que dispara el aviso; en modo texto, la duración de cada turno se estima a 2,5 palabras por segundo.
- Una alerta anticipada ocurre antes del turno anotado como solicitud de riesgo.
- Con tan pocos guiones los intervalos de confianza son anchos: sirven para comparar estrategias, no como cifra definitiva.
- Los guiones los escribió el mismo equipo que escribió las reglas; por eso la partición reservada se usa solo para el informe final.
