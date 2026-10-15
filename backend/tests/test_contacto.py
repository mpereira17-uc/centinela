"""Contacto de confianza: se guarda solo en el dispositivo y nada se envía sin que la persona toque."""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

cliente = TestClient(app)
COMUN = Path(__file__).resolve().parents[2] / "frontend" / "comun.js"


def test_el_formulario_pide_consentimiento_y_no_va_al_servidor():
    html = cliente.get("/ayuda.html").text
    i = html.index('id="contacto-confianza"')
    seccion = html[i:html.index("</section>", i)]
    assert 'id="contacto-acepta"' in seccion and "está de acuerdo" in seccion
    assert "solo en este dispositivo" in seccion and "Nada se envía solo" in seccion
    # Ni el formulario ni el código mandan el contacto al servidor
    assert "action=" not in seccion
    js = cliente.get("/comun.js").text
    assert "fetch(" not in js and "innerHTML" not in js


def test_el_boton_esta_en_los_dos_avisos():
    for pagina in ("/", "/llamada.html"):
        html = cliente.get(pagina).text
        assert re.search(r'class="alerta-contacto[^"]*oculto"[^>]*rel="noopener noreferrer"', html), pagina


def _ejecutar(expresion):
    if not shutil.which("node"):
        pytest.skip("node no está instalado")
    programa = f"""
const vm = require("vm"); const fs = require("fs");
const almacen = {{}};
const ctx = {{ window: {{}}, document: {{ addEventListener() {{}}, querySelector() {{ return null; }},
  documentElement: {{ classList: {{ toggle() {{}}, contains() {{ return false; }} }} }} }},
  matchMedia: () => ({{ matches: false }}), JSON, encodeURIComponent,
  localStorage: {{ getItem: (k) => almacen[k] ?? null, setItem: (k, v) => {{ almacen[k] = String(v); }} }} }};
vm.createContext(ctx);
vm.runInContext(fs.readFileSync({json.dumps(str(COMUN))}, "utf8"), ctx);
const C = ctx.window.Centinela;
console.log(JSON.stringify({expresion}));
"""
    salida = subprocess.run(["node", "-e", programa], capture_output=True, text=True, check=True).stdout
    return json.loads(salida)


def test_solo_acepta_celulares_colombianos():
    assert _ejecutar('["300 123 4567", "+57 310-555-1234", "6011234567", "12345", ""].map(C.normalizarCelular)') == [
        "3001234567", "3105551234", None, None, None,
    ]


def test_el_mensaje_no_lleva_la_conversacion():
    texto = _ejecutar('C.textoParaContacto({ nombre: "Ana" }, "Te piden un código o una clave.")')
    assert texto.startswith("Hola Ana, Centinela marcó como posible estafa")
    assert "Te piden un código o una clave." in texto and "No voy a dar códigos" in texto
