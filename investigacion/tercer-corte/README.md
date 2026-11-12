# Tercer corte: protocolo y prueba simulada del plan de análisis (ruta B)

Esta carpeta acompaña el artículo y el póster del tercer corte de Metodología de la Investigación.

**Ruta declarada: B (protocolo con prueba de análisis simulada).** Ninguna cifra de esta carpeta sale de llamadas reales ni del prototipo. Todos los resultados son datos simulados con un modelo explícito, y solo sirven para comprobar que el plan de análisis funciona y para ver qué diferencias alcanzaría a reconocer.

| Archivo | Contenido |
|---|---|
| `Centinela_Articulo_Tercer_Corte.pdf` | Artículo en formato IEEE, con anexos (datos y código, devolución, uso de IA, contribución) |
| `Centinela_Poster_Tercer_Corte_Ruta_B.pdf` | Póster (A0) |
| `simulacion_plan.py` | Script de la simulación: parámetros, semilla y pruebas |
| `resultados/potencia.csv` | Potencia por escenario (una fila por escenario) |
| `resultados/resumen_simulacion.json` | Parámetros, escenarios y el conjunto de ejemplo de la figura 2 |
| `resultados/figura1_*`, `resultados/figura2_*` | Figuras en PDF, PNG y SVG |

## Repetir la simulación

```
pip install numpy scipy matplotlib
python simulacion_plan.py
```

Con la semilla 20261112 se obtienen las mismas cifras (tarda alrededor de un minuto).

## Diccionario de `potencia.csv`

- `n_riesgo`, `n_legitimas`: llamadas de riesgo y legítimas por estrategia en cada conjunto simulado.
- `delta`: mejora real en detección de la acumulación frente a la decisión por fragmento (proporción).
- `delta_fa`: aumento real de falsas alertas de la acumulación (proporción).
- `potencia`: proporción de las 2000 repeticiones en que McNemar exacta, con corrección de Holm (α = 0,05), dio una diferencia a favor de la acumulación.
- `ic_inf`, `ic_sup`: IC 95 % de Monte Carlo de la potencia.
- `concluye_preferible`: proporción de repeticiones en que se cumple el criterio de decisión (mejora la detección sin aumento significativo de falsas alertas).
- `error_direccion`: proporción de repeticiones con diferencia significativa a favor de la línea base.

## Licencias

Código: MIT. Datos simulados, figuras, artículo y póster: CC BY 4.0.
