"""Entrena el clasificador TF-IDF + regresión logística y lo guarda como JSON.

    python -m evaluacion.entrenar

Usa solo datos de desarrollo: las frases de datos/entrenamiento/, los turnos de quien
llama de los guiones de desarrollo y los de los guiones sintéticos de desarrollo
(plantillas de uso "entrenamiento"). Los guiones reservados, regionales y sintéticos de
prueba no se tocan; quedan para comparar con las reglas en evaluacion.evaluar.

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
# Frases con modismos de varias regiones; las legítimas usan los mismos modismos
FRASES_REGIONALES = FRASES.with_name("frases-regionales.json")
# Tope de falsas alertas por frase al elegir el umbral con validación cruzada
MAX_FALSAS_POR_FRASE = 0.03


def ejemplos(ruta_frases: Path = FRASES) -> tuple[list[str], list[int]]:
    textos, etiquetas, _ = ejemplos_con_grupos(ruta_frases)
    return textos, etiquetas


def ejemplos_con_grupos(ruta_frases: Path = FRASES) -> tuple[list[str], list[int], list[str]]:
    """Como ejemplos(), con el grupo de cada frase: los turnos de una misma plantilla forman un grupo.

    Las llamadas de una plantilla se parecen mucho entre regiones; si unas quedaran para
    entrenar y otras para validar, la validación cruzada saldría optimista y el umbral, bajo.
    """
    datos = json.loads(Path(ruta_frases).read_text(encoding="utf-8"))
    textos = datos["riesgo"] + datos["legitima"]
    etiquetas = [1] * len(datos["riesgo"]) + [0] * len(datos["legitima"])
    if Path(ruta_frases) == FRASES and FRASES_REGIONALES.exists():
        regionales = json.loads(FRASES_REGIONALES.read_text(encoding="utf-8"))
        textos += [f["texto"] for f in regionales["riesgo"]] + [f["texto"] for f in regionales["legitima"]]
        etiquetas += [1] * len(regionales["riesgo"]) + [0] * len(regionales["legitima"])
    grupos = [f"frase-{i}" for i in range(len(textos))]
    for g in guiones.cargar():
        if g.particion not in guiones.PARTICIONES_ENTRENAMIENTO:
            continue
        for i, t in enumerate(g.turnos):
            if t.hablante != "llamante":
                continue
            if g.es_riesgo and i > g.turno_riesgo:
                continue  # después de la solicitud las frases son ambiguas ("sí, rápido"); no se usan
            textos.append(t.texto)
            etiquetas.append(int(g.es_riesgo and i == g.turno_riesgo))
            grupos.append(f"plantilla-{g.plantilla}" if g.plantilla else f"{g.id}-{i}")
    return textos, etiquetas, grupos


def _vectorizador():
    from sklearn.feature_extraction.text import TfidfVectorizer
    return TfidfVectorizer(analyzer=caracteristicas, sublinear_tf=True, min_df=2)


def _regresion():
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(C=4.0, class_weight="balanced", max_iter=2000)


def elegir_umbral(textos, etiquetas, grupos=None, semilla: int = 0) -> tuple[float, dict]:
    """Elige el umbral con predicciones fuera de muestra (validación cruzada de 5 partes por grupo).

    El umbral se mide sobre las frases escritas a mano. Las sintéticas sí entrenan cada
    parte, pero no cuentan al medir: cada plantilla aparece nueve veces (una por región)
    y una sola frase dudosa pesaría como nueve falsas alertas.
    """
    import numpy as np
    from sklearn.model_selection import StratifiedGroupKFold

    y = np.array(etiquetas)
    grupos = grupos if grupos is not None else [str(i) for i in range(len(y))]
    sintetica = np.array([str(g).startswith("plantilla-") for g in grupos])
    prob = np.zeros(len(y))
    for entrenar, probar in StratifiedGroupKFold(5, shuffle=True, random_state=semilla).split(textos, y, grupos):
        vec = _vectorizador()
        x = vec.fit_transform([textos[i] for i in entrenar])
        reg = _regresion().fit(x, y[entrenar])
        prob[probar] = reg.predict_proba(vec.transform([textos[i] for i in probar]))[:, 1]

    def tasas(pred, filas):
        riesgo, legit = filas & (y == 1), filas & (y == 0)
        return int((pred & riesgo).sum()) / max(1, int(riesgo.sum())), int((pred & legit).sum()) / max(1, int(legit.sum()))

    manual = ~sintetica
    mejor = None
    for umbral in np.arange(0.30, 0.91, 0.01):
        det, fp = tasas(prob >= umbral, manual)
        if fp <= MAX_FALSAS_POR_FRASE and (mejor is None or det > mejor[1]):
            mejor = (float(round(umbral, 2)), det, fp)
    umbral, det, fp = mejor
    validacion = {
        "frases_riesgo": int((manual & (y == 1)).sum()), "frases_legitimas": int((manual & (y == 0)).sum()),
        "deteccion_por_frase": det, "falsas_por_frase": fp,
    }
    if sintetica.any():
        det_s, fp_s = tasas(prob >= umbral, sintetica)
        validacion.update({
            "frases_sinteticas_riesgo": int((sintetica & (y == 1)).sum()),
            "frases_sinteticas_legitimas": int((sintetica & (y == 0)).sum()),
            "deteccion_sinteticas": det_s, "falsas_sinteticas": fp_s,
        })
    return umbral, validacion


def entrenar(ruta_frases: Path = FRASES) -> dict:
    textos, etiquetas, grupos = ejemplos_con_grupos(ruta_frases)
    umbral, validacion = elegir_umbral(textos, etiquetas, grupos)
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
    if "deteccion_sinteticas" in v:
        print(f"Frases sintéticas con la plantilla fuera del entrenamiento: detección {v['deteccion_sinteticas']:.0%}, "
              f"falsas alertas {v['falsas_sinteticas']:.0%} ({v['frases_sinteticas_riesgo']} de riesgo, {v['frases_sinteticas_legitimas']} legítimas)")
    print(f"Modelo: {args.salida} ({len(modelo['vocabulario'])} características)")


if __name__ == "__main__":
    main()
