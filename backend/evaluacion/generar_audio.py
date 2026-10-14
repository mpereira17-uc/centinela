"""Genera el audio de cada guion con voces de Piper, para evaluar la transcripción.

Uso (desde backend/, con requirements-ml.txt instalado y voces descargadas):

    python -m evaluacion.generar_audio --voz-llamante voces/es_MX-claude-high.onnx \\
        --voz-usuario voces/es_ES-davefx-medium.onnx

Escribe en datos/audio/ un WAV por guion y un JSON con el inicio y el fin de cada turno.
datos/audio/ no se sube al repositorio.
"""
import argparse
import io
import json
import wave
from pathlib import Path

from . import guiones

SALIDA = Path(__file__).resolve().parents[2] / "datos" / "audio"
SILENCIO_ENTRE_TURNOS = 0.6


class Sintetizador:
    """Carga cada voz una sola vez. Piper se importa aquí para no exigirlo en las pruebas."""

    def __init__(self):
        self._voces = {}

    def __call__(self, texto: str, ruta_voz: str) -> bytes:
        if ruta_voz not in self._voces:
            from piper import PiperVoice
            self._voces[ruta_voz] = PiperVoice.load(ruta_voz)
        buffer = io.BytesIO()
        with wave.open(buffer, "wb") as wav:
            self._voces[ruta_voz].synthesize_wav(texto, wav)
        return buffer.getvalue()


def _leer(wav_bytes: bytes) -> tuple[bytes, tuple[int, int, int]]:
    with wave.open(io.BytesIO(wav_bytes)) as w:
        return w.readframes(w.getnframes()), (w.getnchannels(), w.getsampwidth(), w.getframerate())


def generar(guion: guiones.Guion, voces: dict[str, str], sintetizar, salida: Path) -> dict:
    """Une los turnos con silencios y devuelve la línea de tiempo de cada turno."""
    partes, linea, formato, t = [], [], None, 0.0
    for i, turno in enumerate(guion.turnos):
        cuadros, fmt = _leer(sintetizar(turno.texto, voces[turno.hablante]))
        if formato is None:
            formato = fmt
        elif fmt != formato:
            raise ValueError("Las dos voces deben tener el mismo formato de audio (canales, bits y frecuencia).")
        canales, ancho, frecuencia = formato
        duracion = len(cuadros) / (canales * ancho * frecuencia)
        linea.append({"indice": i, "hablante": turno.hablante, "inicio": round(t, 3), "fin": round(t + duracion, 3)})
        silencio = b"\x00" * int(SILENCIO_ENTRE_TURNOS * frecuencia) * canales * ancho
        partes += [cuadros, silencio]
        t += duracion + SILENCIO_ENTRE_TURNOS

    salida.mkdir(parents=True, exist_ok=True)
    canales, ancho, frecuencia = formato
    with wave.open(str(salida / f"{guion.id}.wav"), "wb") as w:
        w.setnchannels(canales)
        w.setsampwidth(ancho)
        w.setframerate(frecuencia)
        w.writeframes(b"".join(partes))
    meta = {"id": guion.id, "voces": voces, "turnos": linea}
    (salida / f"{guion.id}.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    return meta


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--voz-llamante", required=True, help="Archivo .onnx de Piper para quien llama")
    p.add_argument("--voz-usuario", help="Archivo .onnx para quien recibe (por defecto, la misma)")
    p.add_argument("--particion", default="todas", choices=["todas", *guiones.PARTICIONES])
    p.add_argument("--salida", type=Path, default=SALIDA)
    args = p.parse_args(argv)

    voces = {"llamante": args.voz_llamante, "usuario": args.voz_usuario or args.voz_llamante}
    sintetizar = Sintetizador()
    lista = guiones.cargar(particion=args.particion)
    for g in lista:
        generar(g, voces, sintetizar, args.salida)
        print(f"{g.id}: listo")
    print(f"{len(lista)} guiones en {args.salida}")


if __name__ == "__main__":
    main()
