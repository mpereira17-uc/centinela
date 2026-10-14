"""Registro seguro: cuentas con PIN (Argon2) o passkey, sesiones revocables y consentimientos.

Mitiga A1, A2, A3, A6, A7 y A18 del modelo de amenazas. Nunca se registran alias, PIN,
tokens ni claves en los logs; solo identificadores internos.
"""
import hashlib
import json
import logging
import secrets
import threading
import time
import uuid
from collections import deque
from typing import Annotated, Any, Literal

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from fastapi import APIRouter, Cookie, Depends, Header, HTTPException, Request, Response
from pydantic import BaseModel, Field, field_validator
from webauthn import (
    generate_authentication_options,
    generate_registration_options,
    options_to_json,
    verify_authentication_response,
    verify_registration_response,
)
from webauthn.helpers import base64url_to_bytes, bytes_to_base64url
from webauthn.helpers.structs import (
    AuthenticatorSelectionCriteria,
    PublicKeyCredentialDescriptor,
    ResidentKeyRequirement,
    UserVerificationRequirement,
)

from .config import ajustes
from .db import conexion

log = logging.getLogger("centinela")

COOKIE = "centinela_sesion"
MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 15 * 60
VIGENCIA_RETO = 5 * 60
MAX_SESIONES_POR_USUARIO = 20
MAX_PASSKEYS_POR_USUARIO = 10
MAX_RETOS = 1000

FINALIDADES = {
    "guardar_historial": "Guardar el historial de mis conversaciones y alertas en este equipo",
    "analisis_conversaciones": "Analizar las conversaciones que escribo o subo",
    "transcripcion_audio": "Convertir en texto el audio que grabo o subo",
    "entrenamiento_modelos": "Usar mis conversaciones, sin datos personales, para mejorar el detector",
    "autenticacion_vocal": "Reconocer mi voz para entrar (no disponible en la beta)",
}
Finalidad = Literal["guardar_historial", "analisis_conversaciones", "transcripcion_audio", "entrenamiento_modelos", "autenticacion_vocal"]
NO_DISPONIBLES = {"autenticacion_vocal"}

_hasher = PasswordHasher()
# Hash de relleno: el tiempo de respuesta es el mismo exista o no el alias (A1)
_HASH_RELLENO = _hasher.hash(secrets.token_hex(8))

ERROR_ENTRADA = "Alias o PIN incorrectos"
ERROR_BLOQUEO = "Demasiados intentos fallidos. Espera 15 minutos e inténtalo de nuevo."


# ---- Defensas comunes ----


def exigir_cabecera(x_centinela: Annotated[str | None, Header()] = None):
    """Las solicitudes que cambian algo deben traer X-Centinela: 1.

    Un formulario de otro sitio no puede añadir cabeceras propias sin pasar por CORS,
    así que esto, sumado a SameSite=Strict, bloquea la falsificación de solicitudes (A3).
    """
    if x_centinela != "1":
        raise HTTPException(status_code=403, detail="Solicitud no permitida")


class LimitePorCliente:
    """Ventana deslizante en memoria por dirección IP (A6)."""

    def __init__(self, maximo: int, ventana: float):
        self.maximo, self.ventana = maximo, ventana
        self._registros: dict[str, deque] = {}
        self._lock = threading.Lock()

    def __call__(self, request: Request):
        cliente = request.client.host if request.client else "desconocido"
        ahora = time.monotonic()
        with self._lock:
            if len(self._registros) > 10_000:
                self._registros.clear()
            marcas = self._registros.setdefault(cliente, deque())
            while marcas and ahora - marcas[0] > self.ventana:
                marcas.popleft()
            if len(marcas) >= self.maximo:
                raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Espera un minuto.")
            marcas.append(ahora)

    def reiniciar(self):
        with self._lock:
            self._registros.clear()


limite_credenciales = LimitePorCliente(maximo=20, ventana=60)


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class Sesion(BaseModel):
    usuario_id: str
    sesion_id: str


def usuario_actual(centinela_sesion: Annotated[str | None, Cookie()] = None) -> Sesion:
    """Devuelve el dueño de la sesión; cada consulta se autoriza con este dueño (A7)."""
    if not centinela_sesion or len(centinela_sesion) > 100:
        raise HTTPException(status_code=401, detail="Inicia sesión para continuar")
    ahora = time.time()
    with conexion() as con:
        fila = con.execute(
            "SELECT id, usuario_id FROM sesiones WHERE token_hash = ? AND expira > ?",
            (_hash_token(centinela_sesion), ahora),
        ).fetchone()
        if not fila:
            raise HTTPException(status_code=401, detail="Tu sesión terminó. Vuelve a entrar.")
        con.execute("UPDATE sesiones SET ultimo_uso = ? WHERE id = ?", (ahora, fila["id"]))
    return Sesion(usuario_id=fila["usuario_id"], sesion_id=fila["id"])


def sesion_opcional(centinela_sesion: Annotated[str | None, Cookie()] = None) -> Sesion | None:
    """Como usuario_actual, pero sin exigir sesión: las rutas de análisis funcionan sin cuenta."""
    if not centinela_sesion:
        return None
    try:
        return usuario_actual(centinela_sesion)
    except HTTPException:
        return None


def tiene_permiso(usuario_id: str, finalidad: str) -> bool:
    with conexion() as con:
        fila = con.execute(
            "SELECT otorgado FROM consentimientos WHERE usuario_id = ? AND finalidad = ?", (usuario_id, finalidad)
        ).fetchone()
    return bool(fila and fila["otorgado"])


def _crear_sesion(con, usuario_id: str, request: Request, response: Response) -> str:
    ahora = time.time()
    duracion = ajustes.duracion_sesion_horas * 3600
    token = secrets.token_urlsafe(32)
    sesion_id = uuid.uuid4().hex
    dispositivo = (request.headers.get("user-agent") or "Dispositivo desconocido")[:160]
    con.execute("DELETE FROM sesiones WHERE expira <= ?", (ahora,))
    con.execute(
        "INSERT INTO sesiones (id, usuario_id, token_hash, dispositivo, creada, expira, ultimo_uso) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (sesion_id, usuario_id, _hash_token(token), dispositivo, ahora, ahora + duracion, ahora),
    )
    # Se conservan solo las sesiones más recientes de cada usuario
    con.execute(
        "DELETE FROM sesiones WHERE usuario_id = ? AND id NOT IN "
        "(SELECT id FROM sesiones WHERE usuario_id = ? ORDER BY creada DESC LIMIT ?)",
        (usuario_id, usuario_id, MAX_SESIONES_POR_USUARIO),
    )
    response.set_cookie(
        COOKIE, token, max_age=duracion, httponly=True, samesite="strict", secure=ajustes.cookie_segura, path="/"
    )
    return sesion_id


def _borrar_cookie(response: Response):
    response.delete_cookie(COOKIE, httponly=True, samesite="strict", secure=ajustes.cookie_segura, path="/")


# ---- PIN ----

PIN_TRIVIALES = {"123123", "121212", "112233", "123321", "654321", "696969"}


def _pin_trivial(pin: str) -> bool:
    if len(set(pin)) == 1 or pin in PIN_TRIVIALES:
        return True
    pasos = {(int(b) - int(a)) % 10 for a, b in zip(pin, pin[1:])}
    return pasos in ({1}, {9})  # 123456, 987654, 890123...


class DatosRegistro(BaseModel):
    alias: str = Field(min_length=3, max_length=30, pattern=r"^[\w.\- ]+$")
    pin: str = Field(pattern=r"^\d{6,12}$")

    @field_validator("alias")
    @classmethod
    def limpiar_alias(cls, v: str) -> str:
        v = " ".join(v.split())
        if len(v) < 3:
            raise ValueError("El alias debe tener al menos 3 caracteres")
        return v

    @field_validator("pin")
    @classmethod
    def pin_no_trivial(cls, v: str) -> str:
        if _pin_trivial(v):
            raise ValueError("Ese PIN es muy fácil de adivinar. Evita repetidos y secuencias.")
        return v


class DatosEntrada(BaseModel):
    alias: str = Field(min_length=1, max_length=30)
    pin: str = Field(min_length=1, max_length=12)


class ConfirmarPin(BaseModel):
    pin: str = Field(min_length=1, max_length=12)


def _comprobar_pin(con, usuario, pin: str) -> bool:
    """Verifica el PIN aplicando el límite de intentos con bloqueo temporal (A1)."""
    ahora = time.time()
    if usuario["bloqueado_hasta"] > ahora:
        raise HTTPException(status_code=429, detail=ERROR_BLOQUEO)
    try:
        _hasher.verify(usuario["pin_hash"], pin)
    except (VerificationError, InvalidHashError):
        intentos = usuario["intentos_fallidos"] + 1
        bloqueo = ahora + BLOQUEO_SEGUNDOS if intentos >= MAX_INTENTOS else 0
        con.execute(
            "UPDATE usuarios SET intentos_fallidos = ?, bloqueado_hasta = ? WHERE id = ?",
            (0 if bloqueo else intentos, bloqueo, usuario["id"]),
        )
        log.info("cuenta=%s pin_fallido intentos=%d bloqueo=%s", usuario["id"], intentos, bool(bloqueo))
        return False
    nuevo_hash = _hasher.hash(pin) if _hasher.check_needs_rehash(usuario["pin_hash"]) else usuario["pin_hash"]
    con.execute(
        "UPDATE usuarios SET intentos_fallidos = 0, bloqueado_hasta = 0, pin_hash = ? WHERE id = ?",
        (nuevo_hash, usuario["id"]),
    )
    return True


def _confirmar_pin(con, usuario_id: str, pin: str):
    usuario = con.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,)).fetchone()
    if not _comprobar_pin(con, usuario, pin):
        # Se confirma el contador antes de responder con error
        con.commit()
        raise HTTPException(status_code=403, detail="PIN incorrecto")


# ---- Rutas ----

router = APIRouter(prefix="/cuenta", tags=["cuenta"])
cambia = [Depends(exigir_cabecera)]


@router.post("/registro", status_code=201, dependencies=[*cambia, Depends(limite_credenciales)])
def registrar(datos: DatosRegistro, request: Request, response: Response):
    ahora = time.time()
    usuario_id = uuid.uuid4().hex
    with conexion() as con:
        if con.execute("SELECT 1 FROM usuarios WHERE alias = ?", (datos.alias,)).fetchone():
            raise HTTPException(status_code=409, detail="Ese alias ya está en uso. Elige otro.")
        con.execute(
            "INSERT INTO usuarios (id, alias, pin_hash, creado) VALUES (?, ?, ?, ?)",
            (usuario_id, datos.alias, _hasher.hash(datos.pin), ahora),
        )
        # Todos los consentimientos empiezan apagados; la persona decide cada uno
        con.executemany(
            "INSERT INTO consentimientos (usuario_id, finalidad, otorgado, actualizado) VALUES (?, ?, 0, ?)",
            [(usuario_id, f, ahora) for f in FINALIDADES],
        )
        _crear_sesion(con, usuario_id, request, response)
    log.info("cuenta=%s registrada", usuario_id)
    return {"id": usuario_id, "alias": datos.alias}


@router.post("/entrar", dependencies=[*cambia, Depends(limite_credenciales)])
def entrar(datos: DatosEntrada, request: Request, response: Response):
    with conexion() as con:
        usuario = con.execute("SELECT * FROM usuarios WHERE alias = ?", (" ".join(datos.alias.split()),)).fetchone()
        if usuario is None:
            try:
                _hasher.verify(_HASH_RELLENO, datos.pin)
            except VerificationError:
                pass
            raise HTTPException(status_code=401, detail=ERROR_ENTRADA)
        if not _comprobar_pin(con, usuario, datos.pin):
            con.commit()
            raise HTTPException(status_code=401, detail=ERROR_ENTRADA)
        _crear_sesion(con, usuario["id"], request, response)
    log.info("cuenta=%s entrada metodo=pin", usuario["id"])
    return {"alias": usuario["alias"]}


@router.post("/salir", dependencies=cambia)
def salir(response: Response, sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        con.execute("DELETE FROM sesiones WHERE id = ?", (sesion.sesion_id,))
    _borrar_cookie(response)
    return {"ok": True}


@router.get("")
def ver_cuenta(sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        usuario = con.execute("SELECT alias, creado FROM usuarios WHERE id = ?", (sesion.usuario_id,)).fetchone()
        passkeys = con.execute(
            "SELECT id, nombre, creada FROM credenciales WHERE usuario_id = ? ORDER BY creada", (sesion.usuario_id,)
        ).fetchall()
        consentimientos = dict(
            con.execute(
                "SELECT finalidad, otorgado FROM consentimientos WHERE usuario_id = ?", (sesion.usuario_id,)
            ).fetchall()
        )
    return {
        "alias": usuario["alias"],
        "creado": usuario["creado"],
        "passkeys": [dict(p) for p in passkeys],
        "consentimientos": [
            {"finalidad": f, "descripcion": d, "otorgado": bool(consentimientos.get(f, 0)), "disponible": f not in NO_DISPONIBLES}
            for f, d in FINALIDADES.items()
        ],
    }


@router.get("/sesiones")
def ver_sesiones(sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        filas = con.execute(
            "SELECT id, dispositivo, creada, ultimo_uso, expira FROM sesiones "
            "WHERE usuario_id = ? AND expira > ? ORDER BY ultimo_uso DESC",
            (sesion.usuario_id, time.time()),
        ).fetchall()
    return [{**dict(f), "actual": f["id"] == sesion.sesion_id} for f in filas]


@router.delete("/sesiones/{sesion_id}", dependencies=cambia)
def cerrar_sesion(sesion_id: str, response: Response, sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        borradas = con.execute(
            "DELETE FROM sesiones WHERE id = ? AND usuario_id = ?", (sesion_id, sesion.usuario_id)
        ).rowcount
    if not borradas:
        raise HTTPException(status_code=404, detail="Sesión no encontrada")
    if sesion_id == sesion.sesion_id:
        _borrar_cookie(response)
    log.info("cuenta=%s sesion_cerrada", sesion.usuario_id)
    return {"ok": True}


@router.post("/sesiones/cerrar-otras", dependencies=cambia)
def cerrar_otras(sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        n = con.execute(
            "DELETE FROM sesiones WHERE usuario_id = ? AND id != ?", (sesion.usuario_id, sesion.sesion_id)
        ).rowcount
    return {"cerradas": n}


class CambioConsentimiento(BaseModel):
    finalidad: Finalidad
    otorgado: bool


@router.put("/consentimientos", dependencies=cambia)
def cambiar_consentimiento(cambio: CambioConsentimiento, sesion: Sesion = Depends(usuario_actual)):
    if cambio.otorgado and cambio.finalidad in NO_DISPONIBLES:
        raise HTTPException(status_code=422, detail="Esta función no está disponible en la beta")
    with conexion() as con:
        con.execute(
            "INSERT INTO consentimientos (usuario_id, finalidad, otorgado, actualizado) VALUES (?, ?, ?, ?) "
            "ON CONFLICT (usuario_id, finalidad) DO UPDATE SET otorgado = excluded.otorgado, actualizado = excluded.actualizado",
            (sesion.usuario_id, cambio.finalidad, int(cambio.otorgado), time.time()),
        )
        # Retirar el permiso de guardar borra lo que ya estaba guardado
        if cambio.finalidad == "guardar_historial" and not cambio.otorgado:
            con.execute("DELETE FROM llamadas_guardadas WHERE usuario_id = ?", (sesion.usuario_id,))
    log.info("cuenta=%s consentimiento=%s otorgado=%s", sesion.usuario_id, cambio.finalidad, cambio.otorgado)
    return {"finalidad": cambio.finalidad, "otorgado": cambio.otorgado}


@router.post("/eliminar", dependencies=cambia)
def eliminar_cuenta(datos: ConfirmarPin, response: Response, sesion: Sesion = Depends(usuario_actual)):
    """Borra la cuenta y, en cascada, sus sesiones, passkeys, permisos e historial. Pide el PIN (A18)."""
    with conexion() as con:
        _confirmar_pin(con, sesion.usuario_id, datos.pin)
        con.execute("DELETE FROM usuarios WHERE id = ?", (sesion.usuario_id,))
    _borrar_cookie(response)
    log.info("cuenta=%s eliminada", sesion.usuario_id)
    return {"ok": True}


# ---- Passkeys (WebAuthn) ----


def _guardar_reto(con, tipo: str, reto: bytes, usuario_id: str | None) -> str:
    ahora = time.time()
    con.execute("DELETE FROM retos WHERE expira <= ?", (ahora,))
    if con.execute("SELECT COUNT(*) FROM retos").fetchone()[0] >= MAX_RETOS:
        raise HTTPException(status_code=429, detail="Demasiadas solicitudes. Espera un minuto.")
    reto_id = uuid.uuid4().hex
    con.execute(
        "INSERT INTO retos (id, usuario_id, tipo, reto, expira) VALUES (?, ?, ?, ?, ?)",
        (reto_id, usuario_id, tipo, reto, ahora + VIGENCIA_RETO),
    )
    return reto_id


def _usar_reto(con, reto_id: str, tipo: str, usuario_id: str | None) -> bytes:
    """Cada reto sirve una sola vez: se borra al leerlo, valga o no la respuesta (A3)."""
    fila = con.execute(
        "SELECT reto, expira, usuario_id FROM retos WHERE id = ? AND tipo = ?", (reto_id, tipo)
    ).fetchone()
    con.execute("DELETE FROM retos WHERE id = ?", (reto_id,))
    con.commit()
    if not fila or fila["expira"] <= time.time() or fila["usuario_id"] != usuario_id:
        raise HTTPException(status_code=400, detail="El reto venció o ya se usó. Inténtalo de nuevo.")
    return fila["reto"]


class NuevaPasskey(BaseModel):
    reto_id: str = Field(max_length=64)
    credencial: dict[str, Any]
    nombre: str = Field(default="Mi passkey", min_length=1, max_length=40)


class EntradaPasskey(BaseModel):
    reto_id: str = Field(max_length=64)
    credencial: dict[str, Any]


def _limitar_credencial(credencial: dict):
    if len(json.dumps(credencial)) > 20_000:
        raise HTTPException(status_code=413, detail="Credencial demasiado grande")


@router.post("/passkeys/opciones", dependencies=cambia)
def opciones_passkey(sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        alias = con.execute("SELECT alias FROM usuarios WHERE id = ?", (sesion.usuario_id,)).fetchone()["alias"]
        existentes = con.execute("SELECT id FROM credenciales WHERE usuario_id = ?", (sesion.usuario_id,)).fetchall()
        if len(existentes) >= MAX_PASSKEYS_POR_USUARIO:
            raise HTTPException(status_code=409, detail="Ya tienes el máximo de passkeys")
        opciones = generate_registration_options(
            rp_id=ajustes.rp_id,
            rp_name="Centinela",
            user_name=alias,
            user_id=sesion.usuario_id.encode(),
            authenticator_selection=AuthenticatorSelectionCriteria(
                resident_key=ResidentKeyRequirement.REQUIRED,
                user_verification=UserVerificationRequirement.REQUIRED,
            ),
            exclude_credentials=[PublicKeyCredentialDescriptor(id=base64url_to_bytes(f["id"])) for f in existentes],
        )
        reto_id = _guardar_reto(con, "registro", opciones.challenge, sesion.usuario_id)
    return {"reto_id": reto_id, "opciones": json.loads(options_to_json(opciones))}


@router.post("/passkeys", status_code=201, dependencies=cambia)
def guardar_passkey(datos: NuevaPasskey, sesion: Sesion = Depends(usuario_actual)):
    _limitar_credencial(datos.credencial)
    with conexion() as con:
        reto = _usar_reto(con, datos.reto_id, "registro", sesion.usuario_id)
        try:
            verificada = verify_registration_response(
                credential=datos.credencial,
                expected_challenge=reto,
                expected_rp_id=ajustes.rp_id,
                expected_origin=ajustes.origen,
                require_user_verification=True,
            )
        except Exception:
            raise HTTPException(status_code=400, detail="No se pudo verificar la passkey")
        cred_id = bytes_to_base64url(verificada.credential_id)
        if con.execute("SELECT 1 FROM credenciales WHERE id = ?", (cred_id,)).fetchone():
            raise HTTPException(status_code=409, detail="Esa passkey ya está registrada")
        con.execute(
            "INSERT INTO credenciales (id, usuario_id, clave_publica, contador, nombre, creada) VALUES (?, ?, ?, ?, ?, ?)",
            (cred_id, sesion.usuario_id, verificada.credential_public_key, verificada.sign_count, datos.nombre, time.time()),
        )
    log.info("cuenta=%s passkey_registrada", sesion.usuario_id)
    return {"id": cred_id, "nombre": datos.nombre}


@router.post("/passkeys/{credencial_id}/eliminar", dependencies=cambia)
def eliminar_passkey(credencial_id: str, datos: ConfirmarPin, sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        _confirmar_pin(con, sesion.usuario_id, datos.pin)
        borradas = con.execute(
            "DELETE FROM credenciales WHERE id = ? AND usuario_id = ?", (credencial_id, sesion.usuario_id)
        ).rowcount
    if not borradas:
        raise HTTPException(status_code=404, detail="Passkey no encontrada")
    log.info("cuenta=%s passkey_eliminada", sesion.usuario_id)
    return {"ok": True}


@router.post("/passkey/opciones-entrada", dependencies=[*cambia, Depends(limite_credenciales)])
def opciones_entrada():
    # Passkeys descubribles: el navegador ofrece las cuentas guardadas sin pedir el alias
    opciones = generate_authentication_options(
        rp_id=ajustes.rp_id, user_verification=UserVerificationRequirement.REQUIRED
    )
    with conexion() as con:
        reto_id = _guardar_reto(con, "entrada", opciones.challenge, None)
    return {"reto_id": reto_id, "opciones": json.loads(options_to_json(opciones))}


@router.post("/passkey/entrar", dependencies=[*cambia, Depends(limite_credenciales)])
def entrar_con_passkey(datos: EntradaPasskey, request: Request, response: Response):
    _limitar_credencial(datos.credencial)
    with conexion() as con:
        reto = _usar_reto(con, datos.reto_id, "entrada", None)
        cred = con.execute(
            "SELECT * FROM credenciales WHERE id = ?", (str(datos.credencial.get("id", ""))[:1024],)
        ).fetchone()
        if cred is None:
            raise HTTPException(status_code=401, detail="No reconocemos esa passkey")
        try:
            verificada = verify_authentication_response(
                credential=datos.credencial,
                expected_challenge=reto,
                expected_rp_id=ajustes.rp_id,
                expected_origin=ajustes.origen,
                credential_public_key=cred["clave_publica"],
                credential_current_sign_count=cred["contador"],
                require_user_verification=True,
            )
        except Exception:
            raise HTTPException(status_code=401, detail="No reconocemos esa passkey")
        con.execute("UPDATE credenciales SET contador = ? WHERE id = ?", (verificada.new_sign_count, cred["id"]))
        alias = con.execute("SELECT alias FROM usuarios WHERE id = ?", (cred["usuario_id"],)).fetchone()["alias"]
        _crear_sesion(con, cred["usuario_id"], request, response)
    log.info("cuenta=%s entrada metodo=passkey", cred["usuario_id"])
    return {"alias": alias}
