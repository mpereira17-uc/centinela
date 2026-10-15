"""Lo que hace falta para la sustentación: instalar la app desde un enlace y llamar entre redes distintas.

- `GET /webrtc/ice` entrega los servidores STUN y TURN que usa la llamada por Centinela.
  Sin configurarlos, la llamada solo conecta en la misma red, como en la beta.
- `GET /instalar/qr.svg` dibuja el código QR con la dirección pública de la app,
  para que los jurados la abran y la instalen desde su celular.
"""
import io
import logging
import time

import httpx
from fastapi import APIRouter, HTTPException, Request, Response

from .config import ajustes

log = logging.getLogger("centinela")

router = APIRouter(tags=["instalación y llamada entre redes"])

CLOUDFLARE_URL = "https://rtc.live.cloudflare.com/v1/turn/keys/{llave}/credentials/generate-ice-servers"
# Las credenciales temporales duran un día y se renuevan a la mitad
VIDA_CREDENCIALES = 24 * 3600
_cache: dict = {"servidores": None, "vence": 0.0}


def _cloudflare() -> list[dict]:
    if _cache["servidores"] is not None and time.time() < _cache["vence"]:
        return _cache["servidores"]
    r = httpx.post(
        CLOUDFLARE_URL.format(llave=ajustes.cloudflare_turn_llave),
        headers={"Authorization": f"Bearer {ajustes.cloudflare_turn_token}"},
        json={"ttl": VIDA_CREDENCIALES},
        timeout=10,
    )
    r.raise_for_status()
    servidores = r.json()["iceServers"]
    # La versión anterior de la API devolvía un solo servidor en vez de una lista
    if isinstance(servidores, dict):
        servidores = [servidores]
    _cache.update(servidores=servidores, vence=time.time() + VIDA_CREDENCIALES / 2)
    return servidores


def servidores_ice() -> list[dict]:
    servidores: list[dict] = []
    if ajustes.stun_url:
        servidores.append({"urls": ajustes.stun_url})
    if ajustes.turn_url:
        servidores.append({"urls": ajustes.turn_url, "username": ajustes.turn_usuario, "credential": ajustes.turn_clave})
    if ajustes.cloudflare_turn_llave and ajustes.cloudflare_turn_token:
        try:
            servidores.extend(_cloudflare())
        except (httpx.HTTPError, KeyError, ValueError) as e:
            # Sin TURN la llamada sigue funcionando en la misma red; nunca se registran las claves
            log.warning("turn_cloudflare=no_disponible error=%s", type(e).__name__)
    return servidores


@router.get("/webrtc/ice")
def ice():
    servidores = servidores_ice()
    return {"iceServers": servidores, "entre_redes": any("turn" in str(s.get("urls")) for s in servidores)}


@router.get("/instalar/qr.svg")
def qr(request: Request):
    try:
        import segno
    except ImportError:
        raise HTTPException(status_code=503, detail="Falta instalar segno para dibujar el código QR")
    # La dirección pública que se configuró al arrancar; si no hay, la que usa quien abre la página
    direccion = ajustes.origen if ajustes.origen.startswith("https://") else str(request.base_url).rstrip("/")
    salida = io.BytesIO()
    segno.make(f"{direccion}/instalar.html", error="m").save(salida, kind="svg", scale=8, border=2, dark="#1b2f4b")
    return Response(salida.getvalue(), media_type="image/svg+xml", headers={"Cache-Control": "no-store"})
