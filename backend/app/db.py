"""Base de datos SQLite local. Todas las consultas usan parámetros (modelo de amenazas, A4)."""
import sqlite3
import threading
from contextlib import contextmanager

from .config import ajustes

ESQUEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS usuarios (
    id TEXT PRIMARY KEY,
    alias TEXT NOT NULL UNIQUE COLLATE NOCASE,
    pin_hash TEXT NOT NULL,
    intentos_fallidos INTEGER NOT NULL DEFAULT 0,
    bloqueado_hasta REAL NOT NULL DEFAULT 0,
    creado REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sesiones (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    token_hash TEXT NOT NULL UNIQUE,
    dispositivo TEXT NOT NULL,
    creada REAL NOT NULL,
    expira REAL NOT NULL,
    ultimo_uso REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS credenciales (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    clave_publica BLOB NOT NULL,
    contador INTEGER NOT NULL,
    nombre TEXT NOT NULL,
    creada REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS consentimientos (
    usuario_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    finalidad TEXT NOT NULL,
    otorgado INTEGER NOT NULL,
    actualizado REAL NOT NULL,
    PRIMARY KEY (usuario_id, finalidad)
);
CREATE TABLE IF NOT EXISTS llamadas_guardadas (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    creada REAL NOT NULL,
    actualizada REAL NOT NULL,
    nivel_max TEXT NOT NULL DEFAULT 'bajo',
    aviso_visible INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS llamadas_por_usuario ON llamadas_guardadas (usuario_id, creada);
CREATE TABLE IF NOT EXISTS fragmentos_guardados (
    id TEXT PRIMARY KEY,
    llamada_id TEXT NOT NULL REFERENCES llamadas_guardadas(id) ON DELETE CASCADE,
    orden INTEGER NOT NULL,
    datos TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS fragmentos_por_llamada ON fragmentos_guardados (llamada_id, orden);
CREATE TABLE IF NOT EXISTS secretos (
    nombre TEXT PRIMARY KEY,
    valor BLOB NOT NULL
);
CREATE TABLE IF NOT EXISTS reportes (
    id TEXT PRIMARY KEY,
    usuario_id TEXT NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    numero_ref TEXT NOT NULL,
    terminacion TEXT NOT NULL,
    categoria TEXT NOT NULL,
    creado REAL NOT NULL,
    resultado TEXT NOT NULL DEFAULT 'intento',
    respaldado INTEGER NOT NULL DEFAULT 0,
    UNIQUE (usuario_id, numero_ref)
);
CREATE INDEX IF NOT EXISTS reportes_por_numero ON reportes (numero_ref, creado);
-- Cómo terminó una llamada analizada, contado por quien la recibió. Sin cuenta, número ni texto:
-- solo sirve para medir aciertos y falsas alarmas fuera del laboratorio.
CREATE TABLE IF NOT EXISTS desenlaces (
    id TEXT PRIMARY KEY,
    creado REAL NOT NULL,
    nivel_max TEXT NOT NULL,
    aviso INTEGER NOT NULL,
    resultado TEXT NOT NULL
);
-- Cuándo avisó cada estrategia en cada llamada, para las cifras del documento. Sin texto, número ni cuenta.
CREATE TABLE IF NOT EXISTS metricas_llamadas (
    id TEXT PRIMARY KEY,
    creada REAL NOT NULL,
    origen TEXT NOT NULL,
    proyectada INTEGER NOT NULL DEFAULT 0,
    fragmentos INTEGER NOT NULL,
    alertas TEXT NOT NULL,
    niveles TEXT NOT NULL,
    respuesta_media REAL,
    desenlace TEXT
);
CREATE TABLE IF NOT EXISTS retos (
    id TEXT PRIMARY KEY,
    usuario_id TEXT REFERENCES usuarios(id) ON DELETE CASCADE,
    tipo TEXT NOT NULL,
    reto BLOB NOT NULL,
    expira REAL NOT NULL
);
"""

# Columnas agregadas después de crear la tabla en bases ya existentes
MIGRACIONES = {
    "reportes": [
        ("resultado", "TEXT NOT NULL DEFAULT 'intento'"),
        ("respaldado", "INTEGER NOT NULL DEFAULT 0"),
    ],
}


def _migrar(con):
    for tabla, columnas in MIGRACIONES.items():
        existentes = {f[1] for f in con.execute(f"PRAGMA table_info({tabla})")}
        for nombre, tipo in columnas:
            if nombre not in existentes:
                con.execute(f"ALTER TABLE {tabla} ADD COLUMN {nombre} {tipo}")


_lock = threading.Lock()
_inicializada: set[str] = set()


@contextmanager
def conexion():
    """Abre una conexión con claves foráneas activas y confirma al salir sin errores."""
    ruta = ajustes.base_datos
    con = sqlite3.connect(ruta)
    con.row_factory = sqlite3.Row
    try:
        con.execute("PRAGMA foreign_keys = ON")
        if ruta not in _inicializada:
            with _lock:
                con.executescript(ESQUEMA)
                _migrar(con)
                _inicializada.add(ruta)
        yield con
        con.commit()
    except Exception:
        con.rollback()
        raise
    finally:
        con.close()
