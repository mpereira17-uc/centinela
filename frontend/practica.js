"use strict";

// Modo práctica. Todo el texto se inserta con textContent, nunca como HTML (A5).

const $ = (sel) => document.querySelector(sel);
const CLAVE_MEJOR = "centinela-practica-mejor";
const sinMovimiento = matchMedia("(prefers-reduced-motion: reduce)");
const practica = { rondas: [], actual: 0, aciertos: 0, respondida: false, temporizadores: [] };

function leerMejor() {
  try { return Number(localStorage.getItem(CLAVE_MEJOR)) || 0; } catch { return 0; }
}

function guardarMejor(n) {
  try { localStorage.setItem(CLAVE_MEJOR, String(n)); } catch { /* sin almacenamiento */ }
}

function pintarMejor() {
  const mejor = leerMejor();
  $("#mejor-puntaje").textContent = mejor ? `Tu mejor puntaje: ${mejor} de 5.` : "";
}

async function empezar() {
  $("#empezar").disabled = true;
  try {
    const r = await fetch("/practica/rondas?cantidad=5");
    if (!r.ok) throw new Error();
    practica.rondas = await r.json();
  } catch {
    $("#mejor-puntaje").textContent = "No pudimos cargar las llamadas de práctica. Intenta de nuevo.";
    $("#empezar").disabled = false;
    return;
  }
  practica.actual = 0;
  practica.aciertos = 0;
  $("#inicio-practica").classList.add("oculto");
  $("#final").classList.add("oculto");
  $("#ronda").classList.remove("oculto");
  $("#ronda-total").textContent = practica.rondas.length;
  mostrarRonda();
}

function limpiarTemporizadores() {
  practica.temporizadores.forEach(clearTimeout);
  practica.temporizadores = [];
  if ("speechSynthesis" in window) speechSynthesis.cancel();
}

function burbuja(turno, i) {
  const li = document.createElement("li");
  li.className = "frase";
  li.dataset.hablante = turno.hablante === "usuario" ? "usuario" : "llamante";
  li.dataset.indice = i;
  const quien = document.createElement("span");
  quien.className = "frase-quien";
  quien.textContent = turno.hablante === "usuario" ? "Tú" : "Quien llama";
  const texto = document.createElement("p");
  texto.className = "frase-texto";
  texto.textContent = turno.texto;
  li.append(quien, texto);
  return li;
}

function mostrarRonda() {
  limpiarTemporizadores();
  const ronda = practica.rondas[practica.actual];
  practica.respondida = false;
  $("#ronda-numero").textContent = practica.actual + 1;
  $("#barra-progreso").style.setProperty("width", `${(practica.actual / practica.rondas.length) * 100}%`);
  $("#ronda-region").textContent = ronda.region ? `Habla de ${ronda.region}` : "";
  $("#veredicto").classList.add("oculto");
  document.querySelectorAll(".boton-decidir").forEach((b) => { b.disabled = false; b.classList.remove("elegido"); });
  const lista = $("#ronda-conversacion");
  lista.replaceChildren();
  // Las frases aparecen una por una, como en un chat
  const pausa = sinMovimiento.matches ? 0 : 900;
  ronda.turnos.forEach((t, i) => {
    practica.temporizadores.push(setTimeout(() => {
      lista.append(burbuja(t, i));
      $("#escribiendo-practica").classList.toggle("oculto", i === ronda.turnos.length - 1 || !pausa);
    }, i * pausa));
  });
  $("#escribiendo-practica").classList.toggle("oculto", !pausa);
  $("#escuchar").classList.toggle("oculto", !("speechSynthesis" in window));
  $("#ronda-titulo").scrollIntoView({ block: "start", behavior: sinMovimiento.matches ? "instant" : "smooth" });
}

function escuchar() {
  const ronda = practica.rondas[practica.actual];
  speechSynthesis.cancel();
  for (const t of ronda.turnos.filter((t) => t.hablante === "llamante")) {
    const u = new SpeechSynthesisUtterance(t.texto);
    u.lang = "es-CO";
    speechSynthesis.speak(u);
  }
}

function responder(respuesta) {
  if (practica.respondida) return;
  practica.respondida = true;
  limpiarTemporizadores();
  const ronda = practica.rondas[practica.actual];
  // Si respondió antes de que terminaran de salir las frases, se muestran todas
  const lista = $("#ronda-conversacion");
  lista.replaceChildren(...ronda.turnos.map(burbuja));
  $("#escribiendo-practica").classList.add("oculto");
  const acerto = respuesta === ronda.etiqueta;
  if (acerto) practica.aciertos += 1;
  document.querySelectorAll(".boton-decidir").forEach((b) => {
    b.disabled = true;
    b.classList.toggle("elegido", b.dataset.respuesta === respuesta);
  });
  if (ronda.etiqueta === "riesgo" && ronda.turno_riesgo !== null) {
    lista.querySelector(`[data-indice="${ronda.turno_riesgo}"]`)?.classList.add("trampa");
  }
  const caja = $("#veredicto");
  caja.dataset.acerto = acerto ? "si" : "no";
  $("#veredicto-titulo").textContent = acerto ? "¡Bien!" : "Esta vez no";
  $("#veredicto-texto").textContent = ronda.etiqueta === "riesgo"
    ? `Era una estafa. ${ronda.explicacion}`
    : `Era una llamada normal. ${ronda.explicacion}`;
  const pistas = $("#veredicto-pistas");
  pistas.replaceChildren();
  const lineas = ronda.etiqueta === "riesgo"
    ? [...ronda.pistas, ronda.frase_clave ? `La trampa está en: «${ronda.frase_clave}»` : null].filter(Boolean)
    : [];
  for (const p of lineas) {
    const li = document.createElement("li");
    li.textContent = p;
    pistas.append(li);
  }
  $("#siguiente").textContent = practica.actual + 1 < practica.rondas.length ? "Siguiente llamada" : "Ver mi puntaje";
  caja.classList.remove("oculto");
  caja.focus();
}

function siguiente() {
  practica.actual += 1;
  if (practica.actual < practica.rondas.length) { mostrarRonda(); return; }
  terminarPractica();
}

function terminarPractica() {
  limpiarTemporizadores();
  const total = practica.rondas.length;
  const n = practica.aciertos;
  if (n > leerMejor()) guardarMejor(n);
  $("#ronda").classList.add("oculto");
  $("#final-puntaje").textContent = `${n} de ${total}`;
  $("#final-titulo").textContent = n === total ? "¡No te engañan!" : n >= total - 1 ? "¡Muy bien!" : "Vas aprendiendo";
  $("#final-texto").textContent = n === total
    ? "Reconociste todas. Recuerda: ante la duda, cuelga y llama tú por el canal oficial."
    : "Lo más importante: nadie legítimo te pide códigos, claves ni plata con afán por teléfono. Ante la duda, cuelga.";
  const final = $("#final");
  final.classList.remove("oculto");
  final.focus();
  pintarMejor();
}

document.addEventListener("DOMContentLoaded", () => {
  pintarMejor();
  $("#empezar").addEventListener("click", empezar);
  $("#otra-vez").addEventListener("click", () => { $("#empezar").disabled = false; empezar(); });
  $("#siguiente").addEventListener("click", siguiente);
  $("#escuchar").addEventListener("click", escuchar);
  document.querySelectorAll(".boton-decidir").forEach((b) => b.addEventListener("click", () => responder(b.dataset.respuesta)));
});
