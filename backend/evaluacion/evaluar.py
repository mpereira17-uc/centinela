"""Mide qué tan bien avisa Centinela con los guiones anotados.

    python -m evaluacion.evaluar --modo texto              # motor sobre el texto del guion
    python -m evaluacion.evaluar --modo audio              # Piper -> Whisper -> motor

Métricas por estrategia: detección (llamadas de riesgo con aviso), falsas alertas
(llamadas legítimas con aviso), precisión, tiempo de aviso desde que empieza la
solicitud de riesgo y, en modo audio, la tasa de error de palabra (WER) de la
transcripción. Escribe un JSON y un informe en Markdown en datos/resultados/.
"""
import argparse
import io
import json
import time
import wave
from datetime import datetime, timezone
from pathlib import Path

from . import guiones as g_mod
from .metricas import mediana, wer, wilson
from .motor import Tramo, correr, estrategias_reglas, tramos_de_texto

RESULTADOS = Path(__file__).resolve().parents[2] / "datos" / "resultados"
AUDIO = Path(__file__).resolve().parents[2] / "datos" / "audio"


def _recortar(ruta_wav: Path, inicio: float, fin: float) -> bytes:
    with wave.open(str(ruta_wav)) as w:
        f = w.getframerate()
        w.setpos(int(inicio * f))
        cuadros = w.readframes(int((fin - inicio) * f))
        params = w.getparams()
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as salida:
        salida.setparams(params)
        salida.writeframes(cuadros)
    return buffer.getvalue()


def tramos_de_audio(guion, carpeta: Path, transcribir) -> tuple[list[Tramo], int, int, list[dict], str]:
    """Transcribe cada turno de quien llama y suma el tiempo de transcripción al momento del aviso."""
    meta = json.loads((carpeta / f"{guion.id}.json").read_text(encoding="utf-8"))
    tramos, errores, palabras, detalle = [], 0, 0, []
    for t in meta["turnos"]:
        if t["hablante"] != "llamante":
            continue
        inicio_proc = time.perf_counter()
        segmentos = transcribir(_recortar(carpeta / f"{guion.id}.wav", t["inicio"], t["fin"]))
        demora = time.perf_counter() - inicio_proc
        texto = " ".join(s.texto for s in segmentos).strip()
        referencia = guion.turnos[t["indice"]].texto
        e, n = wer(referencia, texto)
        errores, palabras = errores + e, palabras + n
        detalle.append({"indice": t["indice"], "referencia": referencia, "transcripcion": texto, "segundos_transcripcion": round(demora, 2)})
        tramos.append(Tramo(t["indice"], texto, t["inicio"], t["fin"] + demora))
    return tramos, errores, palabras, detalle, meta["voces"]["llamante"]


def evaluar(lista, modo: str = "texto", estrategias=None, carpeta_audio: Path = AUDIO, transcribir=None) -> dict:
    estrategias = estrategias or estrategias_reglas()
    por_guion, errores_total, palabras_total, por_voz = [], 0, 0, {}
    for guion in lista:
        if modo == "audio":
            tramos, e, n, transcripciones, voz = tramos_de_audio(guion, carpeta_audio, transcribir)
            errores_total, palabras_total = errores_total + e, palabras_total + n
            # El error por voz permite revisar si la transcripción falla más con algún tipo de voz (A14)
            acumulado = por_voz.setdefault(Path(voz).name, [0, 0])
            acumulado[0] += e
            acumulado[1] += n
        else:
            tramos, transcripciones = tramos_de_texto(guion), None
        inicio_riesgo = next((t.inicio for t in tramos if t.indice == guion.turno_riesgo), None)
        fila = {"id": guion.id, "etiqueta": guion.etiqueta, "categoria": guion.categoria, "estrategias": {}}
        for r in correr(tramos, estrategias):
            fila["estrategias"][r.estrategia] = {
                "alerta": r.alerta,
                "turno_alerta": r.indice_alerta,
                "anticipada": bool(r.alerta and guion.es_riesgo and r.indice_alerta < guion.turno_riesgo),
                "segundos_hasta_aviso": (
                    round(max(0.0, r.fin_alerta - inicio_riesgo), 2) if r.alerta and guion.es_riesgo else None
                ),
                "niveles": r.niveles,
            }
        if transcripciones is not None:
            fila["transcripciones"] = transcripciones
        por_guion.append(fila)

    resumen = {}
    for e in estrategias:
        filas = [(f, f["estrategias"][e.nombre]) for f in por_guion]
        riesgo = [d for f, d in filas if f["etiqueta"] == "riesgo"]
        legit = [d for f, d in filas if f["etiqueta"] == "legitima"]
        vp = sum(d["alerta"] for d in riesgo)
        fp = sum(d["alerta"] for d in legit)
        tiempos = [d["segundos_hasta_aviso"] for d in riesgo if d["segundos_hasta_aviso"] is not None]
        resumen[e.nombre] = {
            "llamadas_riesgo": len(riesgo),
            "detectadas": vp,
            "deteccion": vp / len(riesgo) if riesgo else None,
            "deteccion_ic95": wilson(vp, len(riesgo)),
            "llamadas_legitimas": len(legit),
            "falsas_alertas": fp,
            "tasa_falsas_alertas": fp / len(legit) if legit else None,
            "falsas_alertas_ic95": wilson(fp, len(legit)),
            "precision": vp / (vp + fp) if vp + fp else None,
            "alertas_anticipadas": sum(d["anticipada"] for d in riesgo),
            "segundos_hasta_aviso_mediana": mediana(tiempos),
            "segundos_hasta_aviso_max": max(tiempos) if tiempos else None,
            "no_detectadas": [f["id"] for f, d in filas if f["etiqueta"] == "riesgo" and not d["alerta"]],
            "con_falsa_alerta": [f["id"] for f, d in filas if f["etiqueta"] == "legitima" and d["alerta"]],
        }
    salida = {"modo": modo, "guiones": len(lista), "resumen": resumen, "por_guion": por_guion}
    if modo == "audio":
        salida["wer"] = errores_total / palabras_total if palabras_total else None
        salida["wer_por_voz"] = {v: (e / n if n else None) for v, (e, n) in por_voz.items()}
    return salida


def _seg(x):
    return "—" if x is None else f"{x:.1f} s".replace(".", ",")


def _pct(x):
    return "—" if x is None else f"{x * 100:.0f} %"


def _ic(par):
    return "—" if not par else f"{par[0] * 100:.0f}–{par[1] * 100:.0f} %"


def informe(res: dict, particion: str) -> str:
    fecha = res.get("fecha", "")
    lineas = [
        f"# Evaluación en modo {res['modo']} ({particion})",
        "",
        f"Generado por `python -m evaluacion.evaluar` el {fecha}. {res['guiones']} guiones de "
        "[datos/guiones/guiones.json](../guiones/guiones.json). Solo se analizan los turnos de quien llama, como en la llamada simulada.",
        "",
        "| Estrategia | Detección | IC 95 % | Falsas alertas | IC 95 % | Precisión | Aviso (mediana) | Aviso (máx.) |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for nombre, r in res["resumen"].items():
        med = r["segundos_hasta_aviso_mediana"]
        mx = r["segundos_hasta_aviso_max"]
        lineas.append(
            f"| {nombre} | {r['detectadas']}/{r['llamadas_riesgo']} ({_pct(r['deteccion'])}) | {_ic(r['deteccion_ic95'])} "
            f"| {r['falsas_alertas']}/{r['llamadas_legitimas']} ({_pct(r['tasa_falsas_alertas'])}) | {_ic(r['falsas_alertas_ic95'])} "
            f"| {_pct(r['precision'])} | {_seg(med)} | {_seg(mx)} |"
        )
    if res.get("wer") is not None:
        lineas += ["", f"Tasa de error de palabra de la transcripción (WER): **{res['wer'] * 100:.1f} %**.".replace(".", ",", 1)]
        for voz, w in res.get("wer_por_voz", {}).items():
            lineas.append(f"- Voz de quien llama `{voz}`: {'—' if w is None else f'{w * 100:.1f} %'.replace('.', ',')}")
    lineas += ["", "## Errores", ""]
    for nombre, r in res["resumen"].items():
        lineas.append(f"- **{nombre}**: no detectadas {', '.join(r['no_detectadas']) or 'ninguna'}; "
                      f"falsas alertas {', '.join(r['con_falsa_alerta']) or 'ninguna'}; "
                      f"alertas anticipadas {r['alertas_anticipadas']}.")
    lineas += [
        "",
        "## Por guion",
        "",
        "| Guion | Etiqueta | Categoría | " + " | ".join(res["resumen"]) + " |",
        "|---|---|---|" + "---|" * len(res["resumen"]),
    ]
    for f in res["por_guion"]:
        celdas = []
        for nombre in res["resumen"]:
            d = f["estrategias"][nombre]
            if d["alerta"]:
                extra = f", {_seg(d['segundos_hasta_aviso'])}" if d["segundos_hasta_aviso"] is not None else ""
                celdas.append(f"aviso en turno {d['turno_alerta']}{extra}")
            else:
                celdas.append("sin aviso")
        lineas.append(f"| {f['id']} | {f['etiqueta']} | {f['categoria']} | " + " | ".join(celdas) + " |")
    lineas += [
        "",
        "## Cómo leerlo",
        "",
        "- Los tiempos se miden desde que empieza el turno con la solicitud de riesgo hasta que termina el turno que dispara el aviso"
        + (" más lo que tardó la transcripción." if res["modo"] == "audio" else "; en modo texto, la duración de cada turno se estima a 2,5 palabras por segundo."),
        "- Una alerta anticipada ocurre antes del turno anotado como solicitud de riesgo.",
        "- Con tan pocos guiones los intervalos de confianza son anchos: sirven para comparar estrategias, no como cifra definitiva.",
        "- Los guiones los escribió el mismo equipo que escribió las reglas; por eso la partición reservada se usa solo para el informe final.",
    ]
    return "\n".join(lineas) + "\n"


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--modo", choices=["texto", "audio"], default="texto")
    p.add_argument("--particion", default="todas", choices=["todas", *g_mod.PARTICIONES])
    p.add_argument("--audio", type=Path, default=AUDIO, help="Carpeta creada por evaluacion.generar_audio")
    p.add_argument("--salida", type=Path, default=RESULTADOS)
    p.add_argument("--nombre", default="", help="Sufijo del informe, por ejemplo la voz usada")
    args = p.parse_args(argv)

    transcribir = None
    if args.modo == "audio":
        from app.transcripcion import whisper
        transcribir = whisper.transcribir
    res = evaluar(g_mod.cargar(particion=args.particion), args.modo, carpeta_audio=args.audio, transcribir=transcribir)
    res["fecha"] = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    res["particion"] = args.particion

    args.salida.mkdir(parents=True, exist_ok=True)
    base = args.salida / "-".join(filter(None, ["evaluacion", args.modo, args.particion, args.nombre]))
    base.with_suffix(".json").write_text(json.dumps(res, ensure_ascii=False, indent=2), encoding="utf-8")
    base.with_suffix(".md").write_text(informe(res, args.particion), encoding="utf-8")
    for nombre, r in res["resumen"].items():
        print(f"{nombre}: detección {_pct(r['deteccion'])}, falsas alertas {_pct(r['tasa_falsas_alertas'])}")
    print(f"Informe: {base.with_suffix('.md')}")


if __name__ == "__main__":
    main()
