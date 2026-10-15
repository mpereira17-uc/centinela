"""Enciende Centinela para la sustentación con una dirección pública y su código QR.

Uso, desde la carpeta del repositorio:

    python sustentacion.py

1. Abre un túnel gratuito de Cloudflare (cloudflared) que da una dirección https://….trycloudflare.com.
   El HTTPS es obligatorio: sin él, los celulares no dejan usar el micrófono ni instalar la app.
2. Arranca el servidor de Centinela en este portátil, configurado para esa dirección.
3. Muestra la dirección y el código QR que escanean los jurados.

Ctrl+C apaga todo. La dirección cambia cada vez que se arranca, así que el QR se vuelve a mostrar.
Detalle y lista de ensayo en docs/sustentacion.md.
"""
import argparse
import os
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from urllib.parse import urlparse

RAIZ = Path(__file__).resolve().parent
PATRON_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")

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
    parser.add_argument("--sin-navegador", action="store_true", help="No abrir la página de instalación en este portátil")
    parser.add_argument("--espera", type=int, default=45, help="Segundos máximos para obtener la dirección pública")
    args = parser.parse_args()

    if not shutil.which("cloudflared"):
        sys.exit(COMO_INSTALAR)

    print("Abriendo la dirección pública…")
    tunel, url = abrir_tunel(args.puerto, args.espera)

    # El servidor se configura para esa dirección: passkeys, cookies seguras y conexión de la llamada
    entorno = os.environ | {
        "CENTINELA_ORIGEN": url,
        "CENTINELA_RP_ID": urlparse(url).hostname,
        "CENTINELA_COOKIE_SEGURA": "true",
    }
    servidor = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(args.puerto), "--proxy-headers"],
        cwd=RAIZ / "backend", env=entorno,
    )
    time.sleep(3)
    if servidor.poll() is not None:
        tunel.terminate()
        sys.exit("El servidor no arrancó. Revisa el mensaje de arriba (¿instalaste requirements.txt?).")

    print("\nCentinela está encendido.\n")
    print(f"  Dirección para los jurados: {url}")
    print(f"  Página para instalar:       {url}/instalar.html\n")
    mostrar_qr(url)
    print("\nDeja esta ventana abierta durante la demostración. Ctrl+C para apagar.\n")
    if not args.sin_navegador:
        webbrowser.open(f"{url}/instalar.html")

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
