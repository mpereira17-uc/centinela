"""Historial de conversaciones y alertas, con retención limitada, exportación y borrado.

Solo se guarda si la persona entró a su cuenta y activó el permiso "guardar_historial".
Cada consulta filtra por el dueño de la sesión (modelo de amenazas, A7) y el borrado es
real, en cascada (A10).
"""
import json
import logging
import time
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Response

from .config import ajustes
from .cuentas import Sesion, exigir_cabecera, usuario_actual
from .db import conexion
from .modelos import Fragmento, Llamada
from .senales import Nivel

log = logging.getLogger("centinela")

MAX_GUARDADAS_POR_USUARIO = 500


def _ts(dt: datetime) -> float:
    return dt.timestamp()


def _iso(ts: float) -> str:
    return datetime.fromtimestamp(ts, timezone.utc).isoformat()


def purgar(con) -> int:
    """Borra lo que superó la retención configurada."""
    limite = time.time() - ajustes.dias_retencion * 86400
    return con.execute("DELETE FROM llamadas_guardadas WHERE actualizada < ?", (limite,)).rowcount


def guardar_llamada(llamada: Llamada):
    with conexion() as con:
        purgar(con)
        con.execute(
            "INSERT INTO llamadas_guardadas (id, usuario_id, creada, actualizada) VALUES (?, ?, ?, ?)",
            (llamada.id, llamada.dueno, _ts(llamada.creada), time.time()),
        )
        # Se conservan solo las más recientes de cada persona
        con.execute(
            "DELETE FROM llamadas_guardadas WHERE usuario_id = ? AND id NOT IN "
            "(SELECT id FROM llamadas_guardadas WHERE usuario_id = ? ORDER BY creada DESC LIMIT ?)",
            (llamada.dueno, llamada.dueno, MAX_GUARDADAS_POR_USUARIO),
        )


def guardar_fragmento(llamada: Llamada, fragmento: Fragmento):
    """Agrega el fragmento al historial. Si la persona borró la llamada mientras tanto, deja de guardarla."""
    visible = next(d for d in fragmento.decisiones if d.estrategia == ajustes.estrategia_visible)
    with conexion() as con:
        fila = con.execute(
            "SELECT nivel_max FROM llamadas_guardadas WHERE id = ? AND usuario_id = ?", (llamada.id, llamada.dueno)
        ).fetchone()
        if fila is None:
            llamada.guardada = False
            return
        nivel_max = max(Nivel[fila["nivel_max"].upper()], Nivel[visible.nivel.upper()])
        con.execute(
            "INSERT INTO fragmentos_guardados (id, llamada_id, orden, datos) VALUES (?, ?, ?, ?)",
            (fragmento.id, llamada.id, len(llamada.fragmentos), fragmento.model_dump_json()),
        )
        con.execute(
            "UPDATE llamadas_guardadas SET actualizada = ?, nivel_max = ?, aviso_visible = ? WHERE id = ?",
            (time.time(), nivel_max.name.lower(), int(llamada.aviso_visible), llamada.id),
        )


def _resumen(fila) -> dict:
    return {
        "id": fila["id"],
        "creada": _iso(fila["creada"]),
        "nivel_max": fila["nivel_max"],
        "aviso_visible": bool(fila["aviso_visible"]),
        "frases": fila["frases"],
        "borrar_el": _iso(fila["actualizada"] + ajustes.dias_retencion * 86400),
    }


def _listar(con, usuario_id: str) -> list[dict]:
    filas = con.execute(
        "SELECT l.*, (SELECT COUNT(*) FROM fragmentos_guardados f WHERE f.llamada_id = l.id) AS frases "
        "FROM llamadas_guardadas l WHERE l.usuario_id = ? ORDER BY l.creada DESC",
        (usuario_id,),
    ).fetchall()
    return [_resumen(f) for f in filas]


def _fragmentos(con, llamada_id: str) -> list[dict]:
    filas = con.execute(
        "SELECT datos FROM fragmentos_guardados WHERE llamada_id = ? ORDER BY orden", (llamada_id,)
    ).fetchall()
    return [json.loads(f["datos"]) for f in filas]


router = APIRouter(tags=["historial"])


@router.get("/historial")
def ver_historial(sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        purgar(con)
        return {"dias_retencion": ajustes.dias_retencion, "llamadas": _listar(con, sesion.usuario_id)}


@router.get("/historial/{llamada_id}")
def ver_llamada_guardada(llamada_id: str, sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        fila = con.execute(
            "SELECT l.*, (SELECT COUNT(*) FROM fragmentos_guardados f WHERE f.llamada_id = l.id) AS frases "
            "FROM llamadas_guardadas l WHERE l.id = ? AND l.usuario_id = ?",
            (llamada_id, sesion.usuario_id),
        ).fetchone()
        if fila is None:
            raise HTTPException(status_code=404, detail="Conversación no encontrada")
        return {**_resumen(fila), "fragmentos": _fragmentos(con, llamada_id)}


@router.delete("/historial/{llamada_id}", dependencies=[Depends(exigir_cabecera)])
def borrar_llamada_guardada(llamada_id: str, sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        n = con.execute(
            "DELETE FROM llamadas_guardadas WHERE id = ? AND usuario_id = ?", (llamada_id, sesion.usuario_id)
        ).rowcount
    if not n:
        raise HTTPException(status_code=404, detail="Conversación no encontrada")
    log.info("cuenta=%s historial_borrado llamadas=1", sesion.usuario_id)
    return {"borradas": 1}


@router.delete("/historial", dependencies=[Depends(exigir_cabecera)])
def borrar_historial(sesion: Sesion = Depends(usuario_actual)):
    with conexion() as con:
        n = con.execute("DELETE FROM llamadas_guardadas WHERE usuario_id = ?", (sesion.usuario_id,)).rowcount
    log.info("cuenta=%s historial_borrado llamadas=%d", sesion.usuario_id, n)
    return {"borradas": n}


@router.get("/cuenta/exportar")
def exportar(sesion: Sesion = Depends(usuario_actual)):
    """Todos los datos de la persona en un JSON legible (derecho de acceso, Ley 1581 de 2012)."""
    uid = sesion.usuario_id
    with conexion() as con:
        purgar(con)
        usuario = con.execute("SELECT alias, creado FROM usuarios WHERE id = ?", (uid,)).fetchone()
        datos = {
            "exportado": datetime.now(timezone.utc).isoformat(),
            "cuenta": {"alias": usuario["alias"], "creada": _iso(usuario["creado"])},
            "permisos": [
                {"finalidad": f["finalidad"], "otorgado": bool(f["otorgado"]), "actualizado": _iso(f["actualizado"])}
                for f in con.execute("SELECT * FROM consentimientos WHERE usuario_id = ? ORDER BY finalidad", (uid,))
            ],
            "passkeys": [
                {"nombre": p["nombre"], "creada": _iso(p["creada"])}
                for p in con.execute("SELECT nombre, creada FROM credenciales WHERE usuario_id = ? ORDER BY creada", (uid,))
            ],
            "sesiones": [
                {"dispositivo": s["dispositivo"], "creada": _iso(s["creada"]), "ultimo_uso": _iso(s["ultimo_uso"])}
                for s in con.execute("SELECT * FROM sesiones WHERE usuario_id = ? ORDER BY creada", (uid,))
            ],
            "historial": [
                {**r, "fragmentos": _fragmentos(con, r["id"])} for r in _listar(con, uid)
            ],
            "nota": "El PIN, los tokens de sesión y las claves de las passkeys no se exportan: el servidor solo guarda su hash o su parte pública.",
        }
    log.info("cuenta=%s datos_exportados", uid)
    return Response(
        content=json.dumps(datos, ensure_ascii=False, indent=2),
        media_type="application/json",
        headers={"Content-Disposition": 'attachment; filename="centinela-mis-datos.json"', "Cache-Control": "no-store"},
    )
