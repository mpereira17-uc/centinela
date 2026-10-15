"""Entrena el clasificador TF-IDF + regresión logística y lo guarda como JSON.

    python -m evaluacion.entrenar

Usa solo datos de desarrollo: las frases de datos/entrenamiento/frases.json y los
turnos de quien llama de los guiones de desarrollo. Los guiones reservados no se
tocan; quedan para comparar con las reglas en evaluacion.evaluar.

Necesita scikit-learn (requirements-ml.txt). El resultado, backend/app/modelo_clasificador.json,
se aplica sin scikit-learn.
"""
import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from app.clasificador import RUTA_MODELO, caracteristicas

from . import guiones

FRASES = Path(__file__).resolve().parents[2] / "datos" / "entrenamiento" / "frases.json"
# Tope de falsas alertas por frase al elegir el umbral con validación cruzada
MAX_FALSAS_POR_FRASE = 0.03


def ejemplos(ruta_frases: Path = FRASES) -> tuple[list[str], list[int]]:
    datos = json.loads(Path(ruta_frases).read_text(encoding="utf-8"))
    textos = datos["riesgo"] + datos["legitima"]
    etiquetas = [1] * len(datos["riesgo"]) + [0] * len(datos["legitima"])
    for g in guiones.cargar(particion="desarrollo"):
        for i, t in enumerate(g.turnos):
            if t.hablante != "llamante":
                continue
            if g.es_riesgo and i > g.turno_riesgo:
                continue  # después de la solicitud las frases son ambiguas ("sí, rápido"); no se usan
            textos.append(t.texto)
            etiquetas.append(int(g.es_riesgo and i == g.turno_riesgo))
    return textos, etiquetas


def _vectorizador():
    from sklearn.feature_extraction.text import TfidfVectorizer
    return TfidfVectorizer(analyzer=caracteristicas, sublinear_tf=True, min_df=2)


def _regresion():
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(C=4.0, class_weight="balanced", max_iter=2000)


def elegir_umbral(textos, etiquetas, semilla: int = 0) -> tuple[float, dict]:
    """Elige el umbral con predicciones fuera de muestra (validación cruzada de 5 partes)."""
    import numpy as np
    from sklearn.model_selection import StratifiedKFold

    y = np.array(etiquetas)
    prob = np.zeros(len(y))
    for entrenar, probar in StratifiedKFold(5, shuffle=True, random_state=semilla).split(textos, y):
        vec = _vectorizador()
        x = vec.fit_transform([textos[i] for i in entrenar])
        reg = _regresion().fit(x, y[entrenar])
        prob[probar] = reg.predict_proba(vec.transform([textos[i] for i in probar]))[:, 1]

    mejor = None
    for umbral in np.arange(0.30, 0.91, 0.01):
        pred = prob >= umbral
        vp, fp = int((pred & (y == 1)).sum()), int((pred & (y == 0)).sum())
        tasa_fp = fp / int((y == 0).sum())
        if tasa_fp <= MAX_FALSAS_POR_FRASE and (mejor is None or vp > mejor[1]):
            mejor = (float(round(umbral, 2)), vp, fp)
    umbral, vp, fp = mejor
    return umbral, {
        "frases_riesgo": int((y == 1).sum()), "frases_legitimas": int((y == 0).sum()),
        "deteccion_por_frase": vp / int((y == 1).sum()), "falsas_por_frase": fp / int((y == 0).sum()),
    }


def entrenar(ruta_frases: Path = FRASES) -> dict:
    textos, etiquetas = ejemplos(ruta_frases)
    umbral, validacion = elegir_umbral(textos, etiquetas)
    vec = _vectorizador()
    x = vec.fit_transform(textos)
    reg = _regresion().fit(x, etiquetas)
    vocabulario = {str(k): int(v) for k, v in sorted(vec.vocabulary_.items(), key=lambda kv: kv[1])}
    return {
        "version": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "descripcion": "TF-IDF (palabras, pares y trozos de letras) + regresión logística. Entrenado solo con datos de desarrollo.",
        "umbral": umbral,
        "validacion_cruzada": validacion,
        "intercepto": float(reg.intercept_[0]),
        "vocabulario": vocabulario,
        "idf": [round(float(v), 6) for v in vec.idf_],
        "coef": [round(float(v), 6) for v in reg.coef_[0]],
    }


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--salida", type=Path, default=RUTA_MODELO)
    args = p.parse_args(argv)
    modelo = entrenar()
    args.salida.write_text(json.dumps(modelo, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    v = modelo["validacion_cruzada"]
    print(f"Umbral {modelo['umbral']}; validación cruzada por frase: detección {v['deteccion_por_frase']:.0%}, "
          f"falsas alertas {v['falsas_por_frase']:.0%} ({v['frases_riesgo']} frases de riesgo, {v['frases_legitimas']} legítimas)")
    print(f"Modelo: {args.salida} ({len(modelo['vocabulario'])} características)")


if __name__ == "__main__":
    main()
