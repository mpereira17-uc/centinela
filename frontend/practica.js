"use strict";

// Modo práctica. Todo el texto se inserta con textContent, nunca como HTML (A5).

const $ = (sel) => document.querySelector(sel);
const CLAVE_MEJOR = "centinela-practica-mejor";
// Insignias, mejores puntajes por nivel y racha de días. Solo en este dispositivo; el servidor no guarda respuestas.
const CLAVE_PROGRESO = "centinela-practica-progreso";
const PARA_INSIGNIA = 4;
const RONDAS = 5;
const sinMovimiento = matchMedia("(prefers-reduced-motion: reduce)");
const practica = { rondas: [], actual: 0, aciertos: 0, respondida: false, temporizadores: [], nivel: null };
let niveles = [];

function leerMejor() {
  try { return Number(localStorage.getItem(CLAVE_MEJOR)) || 0; } catch { return 0; }
}

function guardarMejor(n) {
  try { localStorage.setItem(CLAVE_MEJOR, String(n)); } catch { /* sin almacenamiento */ }
}

function leerProgreso() {
  let p = null;
  try { p = JSON.parse(localStorage.getItem(CLAVE_PROGRESO)); } catch { /* dañado o sin almacenamiento */ }
  return {
    insignias: Array.isArray(p?.insignias) ? p.insignias.filter((x) => typeof x === "string") : [],
    mejores: p?.mejores && typeof p.mejores === "object" ? p.mejores : {},
    racha: { dias: Number(p?.racha?.dias) || 0, ultimo: typeof p?.racha?.ultimo === "string" ? p.racha.ultimo : "" },
  };
}

function guardarProgreso(p) {
  try { localStorage.setItem(CLAVE_PROGRESO, JSON.stringify(p)); } catch { /* sin almacenamiento */ }
}

// Fecha local como AAAA-MM-DD, para contar días seguidos en la hora del celular
function dia(fecha = new Date()) {
  const dos = (n) => String(n).padStart(2, "0");
  return `${fecha.getFullYear()}-${dos(fecha.getMonth() + 1)}-${dos(fecha.getDate())}`;
}

function ayer() {
  const f = new Date();
  f.setDate(f.getDate() - 1);
  return dia(f);
}

// La racha sigue viva si practicó hoy o ayer; si no, vuelve a cero
function rachaVigente(racha) {
  return racha.ultimo === dia() || racha.ultimo === ayer() ? racha.dias : 0;
}

function sumarDia(progreso) {
  const hoy = dia();
  if (progreso.racha.ultimo === hoy) return;
  progreso.racha = { dias: progreso.racha.ultimo === ayer() ? progreso.racha.dias + 1 : 1, ultimo: hoy };
}

function textoRacha(racha) {
  const dias = rachaVigente(racha);
  if (!dias) return "Practica hoy para empezar una racha.";
  if (racha.ultimo !== dia()) return `Llevas ${dias} ${dias === 1 ? "día" : "días seguidos"}. Practica hoy para no perder la racha.`;
  return dias === 1 ? "Hoy practicaste. Vuelve mañana para empezar una racha." : `Llevas ${dias} días seguidos practicando.`;
}

function pintarRacha() {
  const racha = leerProgreso().racha;
  $("#racha-texto").textContent = textoRacha(racha);
  $("#racha").classList.toggle("encendida", rachaVigente(racha) > 0);
}

function pintarMejor() {
  const mejor = leerMejor();
  $("#mejor-puntaje").textContent = mejor ? `Tu mejor puntaje en la mezcla: ${mejor} de ${RONDAS}.` : "";
}

function insignia(nivel, ganada) {
  const s = document.createElement("span");
  s.className = ganada ? "insignia ganada" : "insignia";
  s.setAttribute("aria-hidden", "true");
  if (ganada) {
    const img = document.createElement("img");
    img.src = "/buho/tranquilo.svg";
    img.alt = "";
    img.width = 44;
    img.height = 44;
    s.append(img);
  } else {
    s.textContent = String(nivel.numero);
  }
  return s;
}

function pintarNiveles() {
  const progreso = leerProgreso();
  const items = niveles.map((n) => {
    const ganada = progreso.insignias.includes(n.id);
    const mejor = Number(progreso.mejores[n.id]) || 0;
    const li = document.createElement("li");
    const b = document.createElement("button");
    b.type = "button";
    b.className = "nivel-practica";
    b.dataset.tactica = n.id;
    const texto = document.createElement("span");
    texto.className = "nivel-practica-texto";
    const titulo = document.createElement("strong");
    titulo.textContent = `Nivel ${n.numero} · ${n.nombre}`;
    const tactica = document.createElement("small");
    tactica.textContent = n.tactica;
    const estado = document.createElement("small");
    estado.className = ganada ? "nivel-practica-estado ganada" : "nivel-practica-estado";
    estado.textContent = ganada
      ? "Insignia ganada"
      : mejor ? `Tu mejor: ${mejor} de ${RONDAS}. La insignia sale con ${PARA_INSIGNIA}.` : `Gana la insignia con ${PARA_INSIGNIA} de ${RONDAS}`;
    texto.append(titulo, tactica, estado);
    b.append(insignia(n, ganada), texto);
    b.addEventListener("click", () => empezar(n.id));
    li.append(b);
    return li;
  });
  $("#niveles").replaceChildren(...items);
  const ganadas = niveles.filter((n) => progreso.insignias.includes(n.id)).length;
  $("#insignias-resumen").textContent = !niveles.length
    ? ""
    : ganadas === niveles.length
      ? `Tienes las ${ganadas} insignias. Sigue practicando de vez en cuando para no olvidarlo.`
      : `Tienes ${ganadas} de ${niveles.length} insignias.`;
}

async function cargarNiveles() {
  try {
    const r = await fetch("/practica/niveles");
    if (!r.ok) throw new Error();
    niveles = await r.json();
  } catch {
    niveles = [];
    $("#insignias-resumen").textContent = "No pudimos cargar los niveles. Puedes practicar con la mezcla de todo.";
  }
  pintarNiveles();
}

async function cargarSemana() {
  try {
    const r = await fetch("/practica/semana");
    if (!r.ok) throw new Error();
    const s = await r.json();
    $("#semana-titulo").textContent = s.titulo;
    $("#semana-lineas").replaceChildren(...s.lineas.map((l) => {
      const li = document.createElement("li");
      li.textContent = l;
      return li;
    }));
    const b = $("#semana-practicar");
    b.textContent = `Practicar esta · ${s.nivel_nombre}`;
    b.dataset.tactica = s.nivel;
    $("#semana").classList.remove("oculto");
  } catch {
    $("#semana").classList.add("oculto");
  }
}

function nombreNivel(id) {
  return niveles.find((n) => n.id === id)?.nombre || "";
}

async function empezar(nivel = null) {
  const botones = document.querySelectorAll("#inicio-practica button, #final button");
  botones.forEach((b) => { b.disabled = true; });
  try {
    const params = new URLSearchParams({ cantidad: String(RONDAS) });
    if (nivel) params.set("nivel", nivel);
    const r = await fetch(`/practica/rondas?${params}`);
    if (!r.ok) throw new Error();
    practica.rondas = await r.json();
  } catch {
    $("#mejor-puntaje").textContent = "No pudimos cargar las llamadas de práctica. Intenta de nuevo.";
    return;
  } finally {
    botones.forEach((b) => { b.disabled = false; });
  }
  practica.nivel = nivel;
  practica.actual = 0;
  practica.aciertos = 0;
  $("#ronda-nivel").textContent = nivel ? `Nivel: ${nombreNivel(nivel)}` : "Mezcla de todo";
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
  const progreso = leerProgreso();
  sumarDia(progreso);
  let nueva = false;
  if (practica.nivel) {
    progreso.mejores[practica.nivel] = Math.max(Number(progreso.mejores[practica.nivel]) || 0, n);
    if (n >= PARA_INSIGNIA && !progreso.insignias.includes(practica.nivel)) {
      progreso.insignias.push(practica.nivel);
      nueva = true;
    }
  } else if (n > leerMejor()) {
    guardarMejor(n);
  }
  guardarProgreso(progreso);
  pintarFinalInsignia(n, nueva, progreso);
  $("#final-racha-texto").textContent = textoRacha(progreso.racha);
  $("#final-racha").classList.toggle("encendida", rachaVigente(progreso.racha) > 0);
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
  pintarRacha();
  pintarNiveles();
}

function siguienteNivel() {
  const i = niveles.findIndex((n) => n.id === practica.nivel);
  return i >= 0 && i + 1 < niveles.length ? niveles[i + 1] : null;
}

function pintarFinalInsignia(n, nueva, progreso) {
  const caja = $("#final-insignia");
  const nivel = practica.nivel;
  caja.classList.toggle("oculto", !nivel || !progreso.insignias.includes(nivel));
  if (nivel) {
    $("#final-insignia-titulo").textContent = nueva ? `¡Ganaste la insignia ${nombreNivel(nivel)}!` : `Insignia ${nombreNivel(nivel)}`;
    $("#final-insignia-texto").textContent = nueva
      ? `Llevas ${progreso.insignias.length} de ${niveles.length || 4}.`
      : "Ya la tenías. Repasar también cuenta para la racha.";
  }
  const otro = siguienteNivel();
  const boton = $("#siguiente-nivel");
  // Pasa al siguiente nivel quien ya tiene la insignia de este; si no, la invitación es a intentarlo otra vez
  const avanza = Boolean(otro) && progreso.insignias.includes(nivel);
  boton.classList.toggle("oculto", !avanza);
  // Un solo botón principal: si puede avanzar, repetir pasa a segundo plano
  $("#otra-vez").classList.toggle("boton-principal", !avanza);
  $("#otra-vez").classList.toggle("boton-secundario", avanza);
  if (otro) {
    boton.textContent = `Siguiente nivel: ${otro.nombre}`;
    boton.dataset.tactica = otro.id;
  }
  $("#otra-vez").textContent = nivel && n < PARA_INSIGNIA ? "Intentar otra vez" : "Practicar otra vez";
}

function elegirNivel() {
  $("#final").classList.add("oculto");
  $("#inicio-practica").classList.remove("oculto");
  $("#niveles-titulo").scrollIntoView({ block: "start", behavior: sinMovimiento.matches ? "instant" : "smooth" });
}

document.addEventListener("DOMContentLoaded", async () => {
  pintarMejor();
  pintarRacha();
  $("#empezar").addEventListener("click", () => empezar());
  $("#otra-vez").addEventListener("click", () => empezar(practica.nivel));
  $("#siguiente-nivel").addEventListener("click", (e) => empezar(e.currentTarget.dataset.tactica));
  $("#elegir-nivel").addEventListener("click", elegirNivel);
  $("#semana-practicar").addEventListener("click", (e) => empezar(e.currentTarget.dataset.tactica || null));
  $("#siguiente").addEventListener("click", siguiente);
  $("#escuchar").addEventListener("click", escuchar);
  document.querySelectorAll(".boton-decidir").forEach((b) => b.addEventListener("click", () => responder(b.dataset.respuesta)));
  await Promise.all([cargarNiveles(), cargarSemana()]);
  // Desde la estafa de la semana del inicio se llega con ?nivel= para empezar de una
  const pedido = new URLSearchParams(location.search).get("nivel");
  if (pedido && niveles.some((n) => n.id === pedido)) {
    history.replaceState(null, "", "/practica.html");
    empezar(pedido);
  }
});
