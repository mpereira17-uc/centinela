# Guiones

[guiones.json](guiones.json) tiene 36 llamadas simuladas en español: 18 de riesgo y 18 legítimas, anotadas según la [guía de anotación](../../docs/guia-anotacion.md). 24 son de desarrollo y 12 están reservadas para el informe final. [guiones-regionales.json](guiones-regionales.json) tiene 12 más con modismos de varias regiones de Colombia (partición `regional`, nunca se usa para entrenar; ver [docs/modismos.md](../../docs/modismos.md)).

El audio generado con Piper (`python -m evaluacion.generar_audio`) va en `datos/audio/`, que no se sube al repositorio. Los resultados de la evaluación están en [datos/resultados/](../resultados/).
