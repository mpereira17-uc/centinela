"use strict";

// Tarjetas de estafador: un guion al azar de la base de Centinela para leerlo en voz alta en la demostración.
// La respuesta (estafa o llamada normal) queda oculta hasta que se pida. Todo texto se inserta con textContent (A5).

const $ = (sel) => document.querySelector(sel);
const QUIEN = { llamante: "Quien llama", usuario: "Quien contesta" };
let numero = 0;
let actual = null;

async function sacar() {
  $("#tarjeta-error").textContent = "";
  const filtro = $("#solo-estafas").checked ? "?etiqueta=riesgo" : "";
  try {
    const r = await fetch(`/guiones/al-azar${filtro}`);
    if (!r.ok) throw new Error(r.status === 429 ? "Muchas tarjetas seguidas. Espera un momento." : "No pudimos sacar una tarjeta.");
    actual = await r.json();
  } catch (e) {
    $("#tarjeta-error").textContent = e instanceof TypeError ? "No pudimos conectar con Centinela." : e.message;
    return;
  }
  numero += 1;
  $("#tarjeta-pista").textContent = `Tarjeta ${numero}${actual.region ? ` · Acento de ${actual.region}` : ""}. Lean cada uno su papel, con pausas como en una llamada.`;
  const lista = $("#turnos");
  lista.replaceChildren();
  for (const t of actual.turnos) {
    const li = document.createElement("li");
    li.dataset.hablante = t.hablante;
    const quien = document.createElement("span");
    quien.className = "guion-quien";
    quien.textContent = QUIEN[t.hablante] || t.hablante;
    const texto = document.createElement("p");
    texto.textContent = t.texto;
    li.append(quien, texto);
    lista.append(li);
  }
  $("#respuesta").classList.add("oculto");
  $("#revelar").classList.remove("oculto");
  $("#tarjeta").classList.remove("oculto");
  $("#tarjeta").scrollIntoView({ block: "start" });
}

function revelar() {
  if (!actual) return;
  const estafa = actual.etiqueta === "riesgo";
  const que = actual.descripcion.charAt(0).toLowerCase() + actual.descripcion.slice(1);
  const p = $("#respuesta");
  p.dataset.estafa = String(estafa);
  p.textContent = estafa
    ? `Era una estafa: ${que}. Centinela debería avisar.`
    : `Era una llamada normal: ${que}. Centinela no debería alarmar.`;
  p.classList.remove("oculto");
  $("#revelar").classList.add("oculto");
}

document.addEventListener("DOMContentLoaded", () => {
  $("#sacar").addEventListener("click", sacar);
  $("#revelar").addEventListener("click", revelar);
});
