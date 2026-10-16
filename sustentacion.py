"""Enciende Centinela para la sustentación con una dirección pública y su código QR.

Uso, desde la carpeta del repositorio:

    python sustentacion.py

1. Abre un túnel gratuito de Cloudflare (cloudflared) que da una dirección https://….trycloudflare.com.
   El HTTPS es obligatorio: sin él, los celulares no dejan usar el micrófono ni instalar la app.
2. Arranca el servidor de Centinela en este portátil, configurado para esa dirección.
3. Muestra la dirección y el código QR que escanean los jurados.
4. Dice si la llamada por Centinela conecta entre redes distintas y deja la voz lista para la primera frase.
5. Abre la pantalla del presentador para el video beam, con una llave nueva en cada arranque.

Ctrl+C apaga todo. La dirección cambia cada vez que se arranca, así que el QR se vuelve a mostrar.
Detalle y lista de ensayo en docs/sustentacion.md.
"""
import argparse
import json
import os
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent
PATRON_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")
# STUN público y gratuito de Cloudflare: ayuda a conectar entre redes aunque falte el TURN
STUN_PUBLICO = "stun:stun.cloudflare.com:3478"

COMO_INSTALAR = """No encontré cloudflared, el programa gratuito que crea la dirección pública.
Instálalo una sola vez y vuelve a correr este comando:
  Windows:  winget install --id Cloudflare.cloudflared
  macOS:    brew install cloudflared
  Linux:    https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/
Luego cierra y abre de nuevo la terminal."""


def abrir_tunel(puerto: int, espera: int) -> tuple[subprocess.Popen, str]:
    tunel = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{puerto}", "--no-autoupdate"],
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8", errors="replace",
    )
    hallada: list[str] = []

    def leer():
        for linea in tunel.stdout:
            if not hallada and (m := PATRON_URL.search(linea)):
                hallada.append(m.group(0))
        # cloudflared sigue escribiendo; se descarta para que no se llene el búfer

    threading.Thread(target=leer, daemon=True).start()
    limite = time.time() + espera
    while not hallada and time.time() < limite and tunel.poll() is None:
        time.sleep(0.2)
    if not hallada:
        tunel.terminate()
        sys.exit("No se pudo abrir el túnel. Revisa la conexión a internet y vuelve a intentarlo.")
    return tunel, hallada[0]


def configurado_en_env(variable: str) -> bool:
    if os.environ.get(variable):
        return True
    env = RAIZ / "backend" / ".env"
    if not env.exists():
        return False
    return any(linea.split("=", 1)[0].strip() == variable for linea in env.read_text(encoding="utf-8", errors="replace").splitlines())


def esperar_servidor(puerto: int, servidor: subprocess.Popen, espera: int = 30) -> bool:
    limite = time.time() + espera
    while time.time() < limite and servidor.poll() is None:
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{puerto}/salud", timeout=2):
                return True
        except OSError:
            time.sleep(0.3)
    return False


def consultar(puerto: int, ruta: str) -> dict:
    try:
        with urllib.request.urlopen(f"http://127.0.0.1:{puerto}{ruta}", timeout=15) as r:
            return json.loads(r.read())
    except (OSError, ValueError):
        return {}


def revisar_llamadas(puerto: int):
    """Cuenta, antes de que lleguen los jurados, qué tan lista está cada parte de las llamadas."""
    ice = consultar(puerto, "/webrtc/ice")
    if ice.get("entre_redes"):
        print("  Llamada por Centinela: lista para conectar entre redes distintas (TURN configurado).")
    else:
        print("  Llamada por Centinela: SIN TURN. Conecta en la misma red y, con suerte, entre algunas redes.")
        print("    Para datos móviles y otro Wi-Fi, pon las claves del TURN en backend/.env (docs/sustentacion.md).")
    voz = consultar(puerto, "/transcripcion/estado")
    if voz.get("estado") == "no_disponible":
        print("  Voz: NO DISPONIBLE. El modo acompañante no podrá escuchar.")
        print(f"    {voz.get('detalle', '')}")
    else:
        print(f"  Voz: cargando el modelo '{voz.get('modelo', 'base')}' para que la primera frase no espere.")
    print("  Revisa cada celular antes de la demo en la página /revisar.html.")


def mostrar_qr(url: str):
    try:
        import segno
    except ImportError:
        print("(Instala segno con pip install -r requirements.txt para ver el QR aquí.)")
        return
    segno.make(f"{url}/instalar.html", error="m").terminal(compact=True)


def main():
    parser = argparse.ArgumentParser(description="Enciende Centinela para la sustentación.")
    parser.add_argument("--puerto", type=int, default=8000)
    parser.add_argument("--sin-navegador", action="store_true", help="No abrir la pantalla del presentador en este portátil")
    parser.add_argument("--demo", action="store_true", help="Carga números de ejemplo ya reportados (ver backend/app/demo.py)")
    parser.add_argument("--espera", type=int, default=45, help="Segundos máximos para obtener la dirección pública")
    args = parser.parse_args()

    if not shutil.which("cloudflared"):
        sys.exit(COMO_INSTALAR)

    if args.demo:
        # Números de ejemplo con reportes, para que la tarjeta de "Posible estafa" se vea en vivo
        subprocess.run([sys.executable, "-m", "app.demo"], cwd=RAIZ / "backend", check=False)

    print("Abriendo la dirección pública…")
    tunel, url = abrir_tunel(args.puerto, args.espera)

    # El servidor se configura para esa dirección: passkeys, cookies seguras y conexión de la llamada
    entorno = os.environ | {
        "CENTINELA_ORIGEN": url,
        "CENTINELA_RP_ID": urlparse(url).hostname,
        "CENTINELA_COOKIE_SEGURA": "true",
        # El modelo de voz se lee al arrancar y no con la primera frase de la demo
        "CENTINELA_PRECARGAR_VOZ": "true",
        # Solo quien tenga este enlace ve la pantalla del presentador
        "CENTINELA_PRESENTADOR_LLAVE": secrets.token_urlsafe(16),
    }
    if not configurado_en_env("CENTINELA_STUN_URL"):
        entorno["CENTINELA_STUN_URL"] = STUN_PUBLICO
    servidor = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(args.puerto), "--proxy-headers"],
        cwd=RAIZ / "backend", env=entorno,
    )
    if not esperar_servidor(args.puerto, servidor):
        tunel.terminate()
        servidor.terminate()
        sys.exit("El servidor no arrancó. Revisa el mensaje de arriba (¿instalaste requirements.txt?).")

    print("\nCentinela está encendido.\n")
    print(f"  Dirección para los jurados: {url}")
    print(f"  Página para instalar:       {url}/instalar.html")
    print(f"  Revisión antes de la demo:  {url}/revisar.html")
    print(f"  Tarjetas de estafador:      {url}/tarjetas.html")
    presentador = f"{url}/presentador.html#llave={entorno['CENTINELA_PRESENTADOR_LLAVE']}"
    print(f"  Pantalla del presentador:   {presentador}")
    print("    (ábrela solo en el portátil: quien tenga ese enlace ve las llamadas que se marquen para mostrar)\n")
    revisar_llamadas(args.puerto)
    print()
    mostrar_qr(url)
    print("\nDeja esta ventana abierta durante la demostración. Ctrl+C para apagar.\n")
    if not args.sin_navegador:
        webbrowser.open(presentador)

    try:
        while servidor.poll() is None and tunel.poll() is None:
            time.sleep(1)
        print("Se detuvo el servidor o el túnel. Vuelve a correr python sustentacion.py.")
    except KeyboardInterrupt:
        print("\nApagando…")
    finally:
        for proceso in (servidor, tunel):
            if proceso.poll() is None:
                proceso.terminate()


if __name__ == "__main__":
    main()
