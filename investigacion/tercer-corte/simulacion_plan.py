"""Prueba del plan de análisis de Centinela con datos SIMULADOS (ruta B).

No usa llamadas ni resultados del prototipo. Genera datos sintéticos con un
modelo explícito para comprobar que las pruebas previstas en el diseño
(Wilson, McNemar exacta, Wilcoxon, bootstrap por llamada y Holm) funcionan
y qué diferencias alcanzaría a detectar la partición reservada
(75 llamadas de riesgo y 75 legítimas).

Uso:  python simulacion_plan.py         (tarda unos minutos)
Salida: carpeta resultados/ (CSV, JSON y figuras PDF/PNG/SVG).
"""
import json
from pathlib import Path

import numpy as np
from scipy.stats import binomtest, wilcoxon, norm
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SEMILLA = 20261112
REPETICIONES = 2000          # conjuntos simulados por escenario
BOOTSTRAP = 10000            # remuestreos de llamadas completas (ejemplo)
ALFA = 0.05

# ---------------- Parámetros del modelo (supuestos, no datos) -------------
P_DET_FRAGMENTO = 0.80       # detección esperada de la línea base (diseño, sec. 5.2)
DISCORDANCIA_INVERSA = 0.02  # llamadas que solo detecta la decisión por fragmento
P_FA_FRAGMENTO = 0.05        # falsas alertas de la línea base
FA_INVERSA = 0.02            # legítimas con falsa alerta solo por fragmento
TIEMPO_MEDIANA_S = 6.0       # mediana del tiempo de aviso de la línea base
TIEMPO_SIGMA_LOG = 0.5       # dispersión lognormal del tiempo de aviso
TIEMPO_RUIDO_S = 1.0         # desviación del cambio de tiempo entre estrategias

DELTAS = [0.00, 0.05, 0.10, 0.15]   # mejora real en detección (máx. 0,18 con base 0,80)
N_RIESGO = [20, 75, 150, 250]             # 20 = prueba preliminar (40 llamadas)
N_PLAN = 75

SALIDA = Path(__file__).with_name("resultados")
# índice del punto, desplazamiento x/y en puntos y alineación de cada etiqueta
POS_ETIQUETA = {20: (3, -4, 9, "right"), 75: (3, 8, 0, "left"),
                150: (2, 8, -8, "left"), 250: (1, -6, 8, "right")}
OKABE_AZUL, OKABE_NARANJA, GRIS = "#0072B2", "#E69F00", "#8C8C8C"


def wilson(k, n, z=1.959964):
    if n == 0:
        return (float("nan"),) * 2
    p = k / n
    den = 1 + z**2 / n
    centro = (p + z**2 / (2 * n)) / den
    margen = z * np.sqrt(p * (1 - p) / n + z**2 / (4 * n**2)) / den
    return centro - margen, centro + margen


def pares(rng, n, p_base, delta, inversa):
    """Resultados pareados (fragmento, acumulación) por llamada.

    Probabilidades conjuntas: ambas = p_base - inversa; solo fragmento =
    inversa; solo acumulación = delta + inversa; ninguna = el resto.
    """
    probs = [p_base - inversa, inversa, delta + inversa,
             1 - p_base - delta - inversa]
    cat = rng.choice(4, size=n, p=probs)
    frag = np.isin(cat, [0, 1])
    acum = np.isin(cat, [0, 2])
    return frag, acum


def simular(rng, n_riesgo, n_legit, delta, delta_fa, cambio_tiempo):
    frag_d, acum_d = pares(rng, n_riesgo, P_DET_FRAGMENTO, delta,
                           DISCORDANCIA_INVERSA)
    frag_fa, acum_fa = pares(rng, n_legit, P_FA_FRAGMENTO, delta_fa, FA_INVERSA)
    t_frag = rng.lognormal(np.log(TIEMPO_MEDIANA_S), TIEMPO_SIGMA_LOG, n_riesgo)
    t_acum = np.clip(t_frag + cambio_tiempo
                     + rng.normal(0, TIEMPO_RUIDO_S, n_riesgo), 0.1, None)
    return dict(frag_d=frag_d, acum_d=acum_d, frag_fa=frag_fa,
                acum_fa=acum_fa, t_frag=t_frag, t_acum=t_acum)


def mcnemar_exacta(a, b):
    solo_b = int(np.sum(b & ~a))
    solo_a = int(np.sum(a & ~b))
    n = solo_a + solo_b
    if n == 0:
        return 1.0, solo_b, solo_a
    return binomtest(solo_b, n, 0.5).pvalue, solo_b, solo_a


def holm(pvals):
    orden = np.argsort(pvals)
    m = len(pvals)
    ajust = np.empty(m)
    prev = 0.0
    for i, j in enumerate(orden):
        prev = max(prev, min(1.0, (m - i) * pvals[j]))
        ajust[j] = prev
    return ajust


def analizar(d):
    p_det, _, _ = mcnemar_exacta(d["frag_d"], d["acum_d"])
    p_fa, _, _ = mcnemar_exacta(d["frag_fa"], d["acum_fa"])
    ambas = d["frag_d"] & d["acum_d"]
    dif = d["t_acum"][ambas] - d["t_frag"][ambas]
    p_t = wilcoxon(dif).pvalue if np.count_nonzero(dif) >= 6 else 1.0
    adj = holm(np.array([p_det, p_fa, p_t]))
    mejora_det = d["acum_d"].mean() > d["frag_d"].mean()
    mas_fa = d["acum_fa"].mean() > d["frag_fa"].mean()
    detecta = adj[0] < ALFA and mejora_det
    preferible = detecta and not (adj[1] < ALFA and mas_fa)
    return detecta, preferible, adj[0] < ALFA and not mejora_det


def potencia(rng, n, delta, delta_fa=0.0, cambio_tiempo=0.0):
    res = np.array([analizar(simular(rng, n, n, delta, delta_fa, cambio_tiempo))
                    for _ in range(REPETICIONES)])
    return res.mean(axis=0)


def mc_ic(p, r=REPETICIONES):
    m = 1.96 * np.sqrt(p * (1 - p) / r)
    return max(0, p - m), min(1, p + m)


def ejemplo(rng):
    """Un conjunto simulado con delta = 0,10 para mostrar la tabla final."""
    d = simular(rng, N_PLAN, N_PLAN, 0.10, 0.0, 0.0)
    out = {}
    for nombre in ("frag", "acum"):
        k = int(d[f"{nombre}_d"].sum())
        kf = int(d[f"{nombre}_fa"].sum())
        out[nombre] = dict(deteccion=k, falsas=kf,
                           ic_det=wilson(k, N_PLAN), ic_fa=wilson(kf, N_PLAN))
    p, sb, sa = mcnemar_exacta(d["frag_d"], d["acum_d"])
    idx = rng.integers(0, N_PLAN, size=(BOOTSTRAP, N_PLAN))
    difs = d["acum_d"][idx].mean(1) - d["frag_d"][idx].mean(1)
    out["mcnemar"] = dict(p=p, solo_acumulacion=sb, solo_fragmento=sa)
    p_fa, sb_fa, sa_fa = mcnemar_exacta(d["frag_fa"], d["acum_fa"])
    out["mcnemar_falsas"] = dict(p=p_fa, solo_acumulacion=sb_fa, solo_fragmento=sa_fa)
    out["dif_bootstrap"] = dict(estimada=float(d["acum_d"].mean() - d["frag_d"].mean()),
                                ic95=[float(np.percentile(difs, 2.5)),
                                      float(np.percentile(difs, 97.5))])
    ambas = d["frag_d"] & d["acum_d"]
    out["tiempo"] = dict(mediana_frag=float(np.median(d["t_frag"][d["frag_d"]])),
                         mediana_acum=float(np.median(d["t_acum"][d["acum_d"]])),
                         wilcoxon_p=float(wilcoxon(d["t_acum"][ambas] - d["t_frag"][ambas]).pvalue))
    return out


def rotulo(ax, arriba=False):
    ax.text(0.01 if arriba else 0.99, 0.97 if arriba else 0.02,
            "DATOS SIMULADOS", transform=ax.transAxes,
            ha="left" if arriba else "right", va="top" if arriba else "bottom", fontsize=9, fontweight="bold", color="#B00020",
            bbox=dict(boxstyle="round,pad=0.25", fc="white", ec="#B00020"))


def limpiar(ax):
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    ax.grid(axis="y", color="#E5E5E5", lw=0.6)
    ax.set_axisbelow(True)


def figura_potencia(tabla):
    fig, ax = plt.subplots(figsize=(6.4, 4.0))
    for n in N_RIESGO:
        filas = [t for t in tabla if t["n_riesgo"] == n and t["delta_fa"] == 0]
        x = [100 * t["delta"] for t in filas]
        y = [100 * t["potencia"] for t in filas]
        lo = [100 * t["potencia_ic"][0] for t in filas]
        hi = [100 * t["potencia_ic"][1] for t in filas]
        plan = n == N_PLAN
        color = OKABE_AZUL if plan else GRIS
        ax.fill_between(x, lo, hi, color=color, alpha=0.18 if plan else 0.10, lw=0)
        ax.plot(x, y, marker="o" if plan else "s", ms=5 if plan else 3.5,
                lw=2.4 if plan else 1.2, color=color,
                ls="-" if plan else "--")
        etiqueta = f"{n} de riesgo" + (" (plan)" if plan else "")
        if n == 20:
            etiqueta += " (prueba preliminar)"
        i, dx, dy, ha = POS_ETIQUETA[n]
        ax.annotate(etiqueta, (x[i], y[i]), xytext=(dx, dy),
                    textcoords="offset points", va="center", ha=ha, fontsize=9,
                    color=color if plan else "#555555",
                    fontweight="bold" if plan else "normal")
    ax.axhline(80, color="#555555", lw=0.8, ls=":")
    ax.text(20.8, 81.5, "potencia de 80 %", fontsize=8, color="#555555", ha="right")
    ax.set_xlim(-0.5, 21)
    ax.set_ylim(0, 100)
    ax.set_xticks([0, 5, 10, 15])
    ax.set_xlabel("Mejora real en detección de la acumulación (puntos porcentuales)")
    ax.set_ylabel("Repeticiones con diferencia\nsignificativa (%)")
    ax.set_title("Con 75 llamadas de riesgo, una mejora de 10 puntos\n"
                 "se detectaría solo en 37 % de los ensayos simulados",
                 fontsize=10.5, loc="left")
    limpiar(ax)
    rotulo(ax, arriba=True)
    fig.text(0.01, 0.005, f"McNemar exacta con corrección de Holm, α = 0,05; "
             f"{REPETICIONES} conjuntos por punto; banda: IC 95 % de Monte Carlo; "
             f"semilla {SEMILLA}.", fontsize=6.5, color="#555555")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    return fig


def figura_ejemplo(ej):
    fig, axes = plt.subplots(1, 2, figsize=(6.4, 2.8))
    nombres = [("frag", "Por fragmento\n(línea base)", GRIS),
               ("acum", "Acumulación\nde indicios", OKABE_AZUL)]
    paneles = ((axes[0], "deteccion", "ic_det",
                "Llamadas de riesgo con alerta (%)", (0, 100)),
               (axes[1], "falsas", "ic_fa",
                "Legítimas con falsa alerta (%)", (0, 25)))
    for j, (ax, clave, ic, titulo, lim) in enumerate(paneles):
        for i, (k, nom, col) in enumerate(nombres):
            v = 100 * ej[k][clave] / N_PLAN
            lo, hi = (100 * a for a in ej[k][ic])
            ax.plot([lo, hi], [i, i], color=col, lw=2)
            ax.plot(v, i, "o", color=col, ms=7)
            izq = j == 0
            ax.annotate(f"{v:.0f} % ({ej[k][clave]}/75)", (lo if izq else hi, i),
                        xytext=(-5 if izq else 5, 0), textcoords="offset points",
                        va="center", ha="right" if izq else "left",
                        fontsize=8, color="#333333")
        ax.set_xlim(*lim)
        ax.set_title(titulo + "\nn = 75 por estrategia", fontsize=8.5, loc="left")
        ax.set_yticks([0, 1])
        ax.set_yticklabels([n for _, n, _ in nombres] if j == 0 else ["", ""],
                           fontsize=8.5)
        ax.set_ylim(-0.6, 1.6)
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)
        ax.tick_params(axis="y", length=0)
    rotulo(axes[1])
    fig.text(0.01, 0.02, "Un conjunto simulado con mejora real de 10 puntos. Punto: proporción; "
             "línea: IC 95 % de Wilson. No son resultados del prototipo.",
             fontsize=7, color="#555555")
    fig.subplots_adjust(left=0.19, right=0.97, top=0.80, bottom=0.2, wspace=0.25)
    return fig


def guardar(fig, nombre):
    for ext in ("pdf", "png", "svg"):
        fig.savefig(SALIDA / f"{nombre}.{ext}", dpi=300)
    plt.close(fig)


def main():
    SALIDA.mkdir(exist_ok=True)
    rng = np.random.default_rng(SEMILLA)
    tabla = []
    escenarios = [(n, d, 0.0) for n in N_RIESGO for d in DELTAS]
    escenarios += [(N_PLAN, d, 0.05) for d in (0.10, 0.15)]
    for n, d, dfa in escenarios:
        pot, pref, inverso = potencia(rng, n, d, dfa)
        tabla.append(dict(n_riesgo=n, n_legitimas=n, delta=d, delta_fa=dfa,
                          potencia=float(pot), potencia_ic=mc_ic(pot),
                          concluye_preferible=float(pref),
                          error_direccion=float(inverso)))
        print(f"n={n:3d} delta={d:.2f} dFA={dfa:.2f} potencia={pot:.3f} "
              f"preferible={pref:.3f}")
    ej = ejemplo(rng)
    margen = {n: (wilson(round(0.8 * n), n)[1] - wilson(round(0.8 * n), n)[0]) / 2
              for n in N_RIESGO}
    resumen = dict(semilla=SEMILLA, repeticiones=REPETICIONES, alfa=ALFA,
                   parametros=dict(p_det_fragmento=P_DET_FRAGMENTO,
                                   discordancia_inversa=DISCORDANCIA_INVERSA,
                                   p_fa_fragmento=P_FA_FRAGMENTO,
                                   fa_inversa=FA_INVERSA,
                                   tiempo_mediana_s=TIEMPO_MEDIANA_S,
                                   tiempo_sigma_log=TIEMPO_SIGMA_LOG,
                                   tiempo_ruido_s=TIEMPO_RUIDO_S),
                   margen_wilson_80=margen, escenarios=tabla, ejemplo=ej)
    (SALIDA / "resumen_simulacion.json").write_text(
        json.dumps(resumen, ensure_ascii=False, indent=2, default=float),
        encoding="utf-8")
    with open(SALIDA / "potencia.csv", "w", encoding="utf-8") as f:
        f.write("n_riesgo,n_legitimas,delta,delta_fa,potencia,ic_inf,ic_sup,"
                "concluye_preferible,error_direccion\n")
        for t in tabla:
            f.write(f"{t['n_riesgo']},{t['n_legitimas']},{t['delta']},"
                    f"{t['delta_fa']},{t['potencia']:.4f},"
                    f"{t['potencia_ic'][0]:.4f},{t['potencia_ic'][1]:.4f},"
                    f"{t['concluye_preferible']:.4f},{t['error_direccion']:.4f}\n")
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9})
    guardar(figura_potencia(tabla), "figura1_potencia_simulada")
    guardar(figura_ejemplo(ej), "figura2_resultado_simulado")
    print(json.dumps(ej, ensure_ascii=False, indent=1, default=float))
    print("margen Wilson:", margen)


if __name__ == "__main__":
    main()
