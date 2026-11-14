"""Mide qué tan bien avisa Centinela con los guiones anotados.

    python -m evaluacion.evaluar --modo texto              # motor sobre el texto del guion
    python -m evaluacion.evaluar --modo audio              # Piper -> Whisper -> motor

Métricas por estrategia: detección (llamadas de riesgo con aviso), falsas alertas
(llamadas legítimas con aviso), precisión, tiempo de aviso desde que empieza la
solicitud de riesgo, demora desde que termina la primera petición riesgosa
(puede ser negativa si avisa antes), avisos tardíos frente a la demora admisible
fijada antes de probar, F1, percentil 95 y, en modo audio, la tasa de error de palabra (WER) de la
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
from .metricas import bootstrap_diferencia, f1, mediana, percentil, wer, wilson
from .motor import Tramo, correr, estrategias_todas, tramos_de_texto

RESULTADOS = Path(__file__).resolve().parents[2] / "datos" / "resultados"
AUDIO = Path(__file__).resolve().parents[2] / "datos" / "audio"
# Segundos que pueden pasar desde que termina la primera petición riesgosa hasta el aviso
# sin que se considere tardío. Se fija antes de probar las estrategias (diseño metodológico).
DEMORA_ADMISIBLE = 5.0
# Pares de estrategias que se comparan llamada a llamada
COMPARACIONES = (("por_fragmento", "acumulacion"), ("clasificador", "hibrida"))


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


def evaluar(lista, modo: str = "texto", estrategias=None, carpeta_audio: Path = AUDIO, transcribir=None,
            demora_admisible: float = DEMORA_ADMISIBLE) -> dict:
    estrategias = estrategias or estrategias_todas()
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
        # Fin de la petición en el audio (sin sumar la transcripción), para medir con el mismo reloj
        fin_riesgo = _fin_hablado(guion, tramos, carpeta_audio if modo == "audio" else None)
        fila = {"id": guion.id, "etiqueta": guion.etiqueta, "categoria": guion.categoria,
                "familia": guion.plantilla or guion.id, "estrategias": {}}
        for r in correr(tramos, estrategias):
            fila["estrategias"][r.estrategia] = {
                "alerta": r.alerta,
                "turno_alerta": r.indice_alerta,
                "anticipada": bool(r.alerta and guion.es_riesgo and r.indice_alerta < guion.turno_riesgo),
                "segundos_hasta_aviso": (
                    round(max(0.0, r.fin_alerta - inicio_riesgo), 2) if r.alerta and guion.es_riesgo else None
                ),
                "demora_aviso": (
                    round(r.fin_alerta - fin_riesgo, 2)
                    if r.alerta and guion.es_riesgo and fin_riesgo is not None else None
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
        demoras = [d["demora_aviso"] for d in riesgo if d["demora_aviso"] is not None]
        for d in riesgo:
            d["tardia"] = d["demora_aviso"] is not None and d["demora_aviso"] > demora_admisible
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
            "f1": f1(vp, fp, len(riesgo) - vp),
            "demora_mediana": mediana(demoras),
            "demora_p95": percentil(demoras, 95),
            "avisos_tardios": sum(d["tardia"] for d in riesgo),
            "alertas_anticipadas": sum(d["anticipada"] for d in riesgo),
            "segundos_hasta_aviso_mediana": mediana(tiempos),
            "segundos_hasta_aviso_max": max(tiempos) if tiempos else None,
            "no_detectadas": [f["id"] for f, d in filas if f["etiqueta"] == "riesgo" and not d["alerta"]],
            "con_falsa_alerta": [f["id"] for f, d in filas if f["etiqueta"] == "legitima" and d["alerta"]],
        }
    salida = {"modo": modo, "guiones": len(lista), "demora_admisible": demora_admisible, "resumen": resumen,
              "comparaciones": comparar(por_guion, [e.nombre for e in estrategias]), "por_guion": por_guion}
    if modo == "audio":
        salida["wer"] = errores_total / palabras_total if palabras_total else None
        salida["wer_por_voz"] = {v: (e / n if n else None) for v, (e, n) in por_voz.items()}
    return salida


def _fin_hablado(guion, tramos, carpeta_audio: Path | None) -> float | None:
    if guion.turno_riesgo is None:
        return None
    if carpeta_audio is not None:
        meta = json.loads((carpeta_audio / f"{guion.id}.json").read_text(encoding="utf-8"))
        return next((t["fin"] for t in meta["turnos"] if t["indice"] == guion.turno_riesgo), None)
    return next((t.fin for t in tramos if t.indice == guion.turno_riesgo), None)


def _ids(por_guion, etiqueta, a, b):
    """Llamadas de la etiqueta donde avisa a y no avisa b."""
    return [f["id"] for f in por_guion if f["etiqueta"] == etiqueta
            and f["estrategias"][a]["alerta"] and not f["estrategias"][b]["alerta"]]


def comparar(por_guion: list[dict], nombres: list[str]) -> list[dict]:
    """Compara dos estrategias sobre las mismas llamadas: en cuáles discrepan y cuánto cambia el resultado."""
    salida = []
    for a, b in COMPARACIONES:
        if a not in nombres or b not in nombres:
            continue
        fila = {"a": a, "b": b}
        for etiqueta, clave in (("riesgo", "deteccion"), ("legitima", "falsas_alertas")):
            grupos: dict[str, list] = {}
            for f in por_guion:
                if f["etiqueta"] == etiqueta:
                    grupos.setdefault(f.get("familia", f["id"]), []).append(
                        (f["estrategias"][a]["alerta"], f["estrategias"][b]["alerta"]))
            fila[clave] = {
                "familias": len(grupos),
                "solo_a": _ids(por_guion, etiqueta, a, b),
                "solo_b": _ids(por_guion, etiqueta, b, a),
                "diferencia_ic95": bootstrap_diferencia(list(grupos.values())),
            }
        # Turno del aviso en las llamadas de riesgo que ambas detectan
        ambas = [(f["estrategias"][a]["turno_alerta"], f["estrategias"][b]["turno_alerta"]) for f in por_guion
                 if f["etiqueta"] == "riesgo" and f["estrategias"][a]["alerta"] and f["estrategias"][b]["alerta"]]
        fila["b_antes"] = sum(tb < ta for ta, tb in ambas)
        fila["a_antes"] = sum(ta < tb for ta, tb in ambas)
        salida.append(fila)
    return salida


def _seg(x):
    return "—" if x is None else f"{x:.1f} s".replace(".", ",")


def _pct(x):
    return "—" if x is None else f"{x * 100:.0f} %"


def _por_familia(ids: list[str], familias: dict[str, str]) -> str:
    """Agrupa las llamadas de una misma plantilla: "gradual_banco_cajero (9 regiones)"."""
    if not ids:
        return "ninguna"
    cuenta: dict[str, int] = {}
    for i in ids:
        cuenta[familias.get(i, i)] = cuenta.get(familias.get(i, i), 0) + 1
    return ", ".join(f if n == 1 else f"{f} ({n} regiones)" for f, n in cuenta.items())


def _dif(t):
    if not t:
        return "—"
    base, bajo, alto = t
    return f"{base * 100:+.1f} pp (IC 95 %: {bajo * 100:+.1f} a {alto * 100:+.1f})".replace(".", ",")


def _ic(par):
    return "—" if not par else f"{par[0] * 100:.0f}–{par[1] * 100:.0f} %"


def informe(res: dict, particion: str) -> str:
    fecha = res.get("fecha", "")
    lineas = [
        f"# Evaluación en modo {res['modo']} ({particion})",
        "",
        f"Generado por `python -m evaluacion.evaluar` el {fecha}. {res['guiones']} guiones de "
        + ("[datos/guiones/guiones-regionales.json](../guiones/guiones-regionales.json)" if particion == "regional" else
           "[datos/guiones/guiones-sinteticos.json](../guiones/guiones-sinteticos.json)" if particion.startswith("sintetica") else
           "[datos/guiones/guiones.json](../guiones/guiones.json)" if particion in ("desarrollo", "reservada") else
           "[datos/guiones/](../guiones/)")
        + ". Solo se analizan los turnos de quien llama, como en la llamada simulada.",
        "",
        "| Estrategia | Detección | IC 95 % | Falsas alertas | IC 95 % | Precisión | F1 | Demora (mediana) "
        "| Demora (p95) | Tardías |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for nombre, r in res["resumen"].items():
        lineas.append(
            f"| {nombre} | {r['detectadas']}/{r['llamadas_riesgo']} ({_pct(r['deteccion'])}) | {_ic(r['deteccion_ic95'])} "
            f"| {r['falsas_alertas']}/{r['llamadas_legitimas']} ({_pct(r['tasa_falsas_alertas'])}) | {_ic(r['falsas_alertas_ic95'])} "
            f"| {_pct(r['precision'])} | {_pct(r['f1'])} | {_seg(r['demora_mediana'])} | {_seg(r['demora_p95'])} "
            f"| {r['avisos_tardios']}/{r['detectadas']} |"
        )
    if res.get("comparaciones"):
        lineas += ["", "## Comparación llamada a llamada", "",
                   "Diferencia = segunda estrategia menos primera, en puntos porcentuales. El intervalo sale de remuestrear "
                   "2000 veces familias completas de llamadas (una plantilla con todas sus regiones cuenta como una sola), "
                   "porque comparten la forma del engaño. Si el intervalo incluye el cero, la diferencia no es concluyente "
                   "con estos guiones.", ""]
        familias = {f["id"]: f.get("familia", f["id"]) for f in res["por_guion"]}
        for c in res["comparaciones"]:
            det, fa = c["deteccion"], c["falsas_alertas"]
            lineas += [
                f"**{c['a']} → {c['b']}**",
                "",
                f"- Detección ({det['familias']} familias de riesgo): {_dif(det['diferencia_ic95'])}. Solo {c['b']}: {_por_familia(det['solo_b'], familias)}; "
                f"solo {c['a']}: {_por_familia(det['solo_a'], familias)}.",
                f"- Falsas alertas ({fa['familias']} familias legítimas): {_dif(fa['diferencia_ic95'])}. Solo {c['b']}: {_por_familia(fa['solo_b'], familias)}; "
                f"solo {c['a']}: {_por_familia(fa['solo_a'], familias)}.",
                f"- Cuando ambas avisan: {c['b']} avisa en un turno anterior en {c['b_antes']} llamadas "
                f"y {c['a']} en {c['a_antes']}.",
                "",
            ]
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
        "- La demora va desde que termina la primera petición riesgosa hasta el aviso. Es negativa si el aviso llega antes; "
        f"es tardía si pasa de {_seg(res.get('demora_admisible'))}, valor fijado antes de probar. La mediana y el percentil 95 "
        "solo cuentan las llamadas detectadas; las no detectadas se listan aparte.",
        "- Los tiempos de la tabla por guion se miden desde que empieza el turno con la solicitud de riesgo hasta que termina el turno que dispara el aviso"
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
    p.add_argument("--demora-admisible", type=float, default=DEMORA_ADMISIBLE,
                   help="Segundos tras la petición riesgosa antes de considerar tardío el aviso")
    args = p.parse_args(argv)

    transcribir = None
    if args.modo == "audio":
        from app.transcripcion import whisper
        transcribir = whisper.transcribir
    res = evaluar(g_mod.cargar(particion=args.particion), args.modo, carpeta_audio=args.audio, transcribir=transcribir,
                  demora_admisible=args.demora_admisible)
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
