"""Modo demostración: números de ejemplo ya reportados por varias personas, para la sustentación.

Sin esto, la franja de "Posible estafa" o "Probable estafa" solo aparece cuando varias cuentas con
más de un día reportan un número, y eso no se consigue en el salón. Los datos de ejemplo:

- Se guardan solo en la base de este portátil y se borran con `python -m app.demo --quitar`.
- Usan cuentas de ejemplo (alias que empiezan por "demo-sustentacion-") a las que nadie puede entrar:
  su PIN es un secreto al azar que no se guarda.
- Usan números con ceros (300 000 0001…) para no señalar el número de una persona real.

Uso, desde backend/:  python -m app.demo   (o `python sustentacion.py --demo` desde la raíz)
"""
import argparse
import secrets
import time
import uuid

from argon2 import PasswordHasher

from .db import conexion
from .reportes import _pesar, _referencia, explicar, normalizar_numero

PREFIJO = "demo-sustentacion-"

# Número, lo que dice cada cuenta de ejemplo y la categoría de lo que hizo quien llamó
NUMEROS = [
    ("300 000 0001", ["perdida", "perdida", "intento"], "suplanta_entidad"),  # Probable estafa
    ("300 000 0002", ["intento", "intento", "intento"], "premio_falso"),  # Posible estafa
    ("601 000 0003", ["publicidad", "publicidad"], "ninguna"),  # Publicidad o call center
]


def _cuentas(con, cuantas: int, ahora: float) -> list[str]:
    hasher = PasswordHasher()
    ids = []
    for i in range(1, cuantas + 1):
        alias = f"{PREFIJO}{i}"
        fila = con.execute("SELECT id FROM usuarios WHERE alias = ?", (alias,)).fetchone()
        if fila:
            ids.append(fila["id"])
            continue
        usuario_id = uuid.uuid4().hex
        # Diez días de antigüedad, para que sus reportes cuenten como los de cualquier persona
        con.execute(
            "INSERT INTO usuarios (id, alias, pin_hash, creado) VALUES (?, ?, ?, ?)",
            (usuario_id, alias, hasher.hash(secrets.token_hex(16)), ahora - 10 * 86400),
        )
        ids.append(usuario_id)
    return ids


def sembrar() -> list[dict]:
    ahora = time.time()
    resumen = []
    with conexion() as con:
        cuentas = _cuentas(con, max(len(r) for _, r, _ in NUMEROS), ahora)
        for numero, resultados, categoria in NUMEROS:
            normal = normalizar_numero(numero)
            ref = _referencia(con, normal)
            for usuario_id, resultado in zip(cuentas, resultados):
                con.execute(
                    """INSERT OR IGNORE INTO reportes (id, usuario_id, numero_ref, terminacion, categoria, creado, resultado)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (uuid.uuid4().hex, usuario_id, ref, normal[-4:], categoria, ahora - 2 * 86400, resultado),
                )
            resumen.append({"numero": numero, **explicar(_pesar(con, ref, ahora))})
    return resumen


def quitar() -> int:
    with conexion() as con:
        # Los reportes de las cuentas de ejemplo se van con ellas (ON DELETE CASCADE)
        return con.execute("DELETE FROM usuarios WHERE alias LIKE ?", (PREFIJO + "%",)).rowcount


def main():
    parser = argparse.ArgumentParser(description="Números de ejemplo para la demostración de Centinela.")
    parser.add_argument("--quitar", action="store_true", help="Borra las cuentas y reportes de ejemplo")
    args = parser.parse_args()
    if args.quitar:
        print(f"Se borraron {quitar()} cuentas de ejemplo y sus reportes.")
        return
    print("Números de ejemplo listos para la demostración (llámalos desde el emulador o reporta otros):")
    for r in sembrar():
        print(f"  {r['numero']}  ->  {r['estado']}")


if __name__ == "__main__":
    main()
