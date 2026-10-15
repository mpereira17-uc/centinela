"use strict";

// Todo el texto se inserta con textContent, nunca como HTML (modelo de amenazas, A5).

const $ = (sel) => document.querySelector(sel);
let grupos = [];

function sinTildes(texto) {
  return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function enlace(href, texto, clase) {
  const a = document.createElement("a");
  a.href = href;
  a.textContent = texto;
  a.className = clase;
  if (href.startsWith("http")) { a.target = "_blank"; a.rel = "noopener noreferrer"; }
  return a;
}

function pintarDirectorio(filtro = "") {
  const buscado = sinTildes(filtro.trim());
  const lista = $("#directorio-lista");
  lista.replaceChildren();
  let total = 0;
  for (const g of grupos) {
    const entradas = g.entradas.filter((e) => !buscado || sinTildes(`${e.nombre} ${e.para || ""}`).includes(buscado));
    if (!entradas.length) continue;
    total += entradas.length;
    const titulo = document.createElement("h3");
    titulo.className = "subtitulo";
    titulo.textContent = g.titulo;
    lista.append(titulo);
    if (g.consejo) {
      const c = document.createElement("p");
      c.className = "ayuda";
      c.textContent = g.consejo;
      lista.append(c);
    }
    const ul = document.createElement("ul");
    ul.className = "directorio";
    for (const e of entradas) {
      const li = document.createElement("li");
      const nombre = document.createElement("strong");
      nombre.textContent = e.nombre;
      li.append(nombre);
      if (e.para) {
        const p = document.createElement("span");
        p.textContent = e.para;
        li.append(p);
      }
      const acciones = document.createElement("div");
      acciones.className = "fila-acciones";
      if (e.telefono) acciones.append(enlace(`tel:${e.telefono}`, `Llamar al ${e.telefono}`, "boton-principal"));
      if (e.web) acciones.append(enlace(e.web, "Página oficial", "boton-secundario"));
      li.append(acciones);
      ul.append(li);
    }
    lista.append(ul);
  }
  $("#directorio-estado").textContent = buscado && !total
    ? "No está en la lista. Busca el canal oficial en tu factura, tu tarjeta o la aplicación de la entidad."
    : "";
}

async function cargarDirectorio() {
  try {
    const r = await fetch("/directorio");
    if (!r.ok) throw new Error();
    const datos = await r.json();
    grupos = datos.grupos;
    $("#directorio-fecha").textContent = `Lista revisada el ${datos.actualizado}. Si un número cambió, la página oficial tiene el correcto.`;
    pintarDirectorio();
  } catch {
    $("#directorio-estado").textContent = "No pudimos cargar el directorio. Mientras tanto: emergencias 123, extorsión 165 (GAULA).";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  cargarDirectorio();
  $("#buscar-entidad").addEventListener("input", (e) => pintarDirectorio(e.target.value));
  if (location.hash) document.querySelector(location.hash)?.scrollIntoView();
});
