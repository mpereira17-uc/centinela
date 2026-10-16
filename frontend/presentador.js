"use strict";

// Pantalla del presentador: muestra en el video beam lo que oye Centinela en el celular de un jurado,
// con las tres estrategias que compara la tesis sobre la misma conversación y en qué frase avisó cada una.
// Necesita la llave que da sustentacion.py en el enlace (#llave=…); se guarda en esta pestaña y se quita
// de la dirección para que no quede proyectada. Todo texto se inserta con textContent (A5).

const $ = (sel) => document.querySelector(sel);
const NOMBRES = { por_fragmento: "Por frase", acumulacion: "Acumulada", hibrida: "Híbrida (modelo)" };
const NIVELES = { bajo: "Bajo", moderado: "Moderado", alto: "Alto", critico: "Crítico" };
const MODOS = { acompanante: "Modo acompañante", llamada: "Llamada por Centinela" };
const DESENLACES = { perdida: "Dijo que lo estafaron", intento: "Dijo que intentaron estafarlo", publicidad: "Dijo que era publicidad", legitima: "Dijo que era una llamada normal" };
const FRASES_A_LA_VISTA = 6;

const estado = { llave: null, desde: 0, estrategias: [], visible: null, llamadas: new Map(), fallos: 0 };

function leerLlave() {
  const enlace = new URLSearchParams(location.hash.slice(1)).get("llave");
  if (enlace) {
    try { sessionStorage.setItem("centinela-presentador", enlace); } catch { /* sigue con la del enlace */ }
    history.replaceState(null, "", location.pathname);
    return enlace;
  }
  try { return sessionStorage.getItem("centinela-presentador"); } catch { return null; }
}

function minutos(s) {
  const t = Math.max(0, Math.round(Number(s) || 0));
  return `${Math.floor(t / 60)}:${String(t % 60).padStart(2, "0")}`;
}

function nombre(e) {
  return NOMBRES[e] || e;
}

// ---- Una tarjeta por llamada ----

function tarjetaDe(n, modo) {
  if (estado.llamadas.has(n)) return estado.llamadas.get(n);
  const art = document.createElement("article");
  art.className = "tarjeta proy-llamada";
  const h = document.createElement("h2");
  h.textContent = `Llamada ${n}`;
  const sub = document.createElement("p");
  sub.className = "ayuda";
  sub.textContent = MODOS[modo] || MODOS.llamada;
  const primeros = document.createElement("div");
  primeros.className = "proy-primeros";
  const frases = document.createElement("ol");
  frases.className = "proy-frases";
  const final = document.createElement("p");
  final.className = "proy-desenlace oculto";
  art.append(h, sub, primeros, frases, final);
  $("#proy-llamadas").prepend(art);
  $("#proy-vacio").classList.add("oculto");
  const llamada = { art, primeros, frases, final, avisos: {} };
  estado.llamadas.set(n, llamada);
  pintarPrimeros(llamada);
  return llamada;
}

// Arriba de cada llamada: en qué frase avisó primero cada estrategia
function pintarPrimeros(llamada) {
  llamada.primeros.replaceChildren();
  for (const e of estado.estrategias) {
    const a = llamada.avisos[e];
    const chip = document.createElement("span");
    chip.className = "proy-primero";
    chip.dataset.aviso = String(Boolean(a));
    if (e === estado.visible) chip.dataset.visible = "true";
    const fuerte = document.createElement("strong");
    fuerte.textContent = nombre(e);
    chip.append(fuerte, a ? ` avisó en la frase ${a.frase} (${minutos(a.segundo)})` : " sin aviso todavía");
    llamada.primeros.append(chip);
  }
}

function agregarFrase(ev) {
  const llamada = tarjetaDe(ev.llamada, null);
  const li = document.createElement("li");
  const texto = document.createElement("p");
  texto.className = "proy-texto";
  texto.textContent = ev.texto;
  const niveles = document.createElement("div");
  niveles.className = "proy-niveles";
  for (const d of ev.decisiones) {
    const chip = document.createElement("span");
    chip.className = "proy-nivel";
    chip.dataset.nivel = d.nivel;
    chip.dataset.alerta = String(d.alerta);
    chip.textContent = `${nombre(d.estrategia)}: ${NIVELES[d.nivel]}${d.alerta ? " · avisa" : ""}`;
    niveles.append(chip);
    if (d.alerta && !llamada.avisos[d.estrategia]) llamada.avisos[d.estrategia] = { frase: ev.frase, segundo: ev.segundo };
  }
  const meta = document.createElement("span");
  meta.className = "proy-meta";
  meta.textContent = `Frase ${ev.frase} · ${minutos(ev.segundo)} · respondió en ${String(ev.respuesta.toFixed(1)).replace(".", ",")} s`;
  li.append(texto, niveles, meta);
  if (ev.aviso) li.classList.add("proy-aviso");
  llamada.frases.append(li);
  while (llamada.frases.children.length > FRASES_A_LA_VISTA) llamada.frases.firstElementChild.remove();
  pintarPrimeros(llamada);
}

function aplicar(ev) {
  if (ev.tipo === "inicio") tarjetaDe(ev.llamada, ev.modo);
  else if (ev.tipo === "frase") agregarFrase(ev);
  else if (ev.tipo === "desenlace") {
    const llamada = tarjetaDe(ev.llamada, null);
    llamada.final.textContent = `Al colgar: ${DESENLACES[ev.resultado] || ev.resultado}.`;
    llamada.final.classList.remove("oculto");
    cifras();
  }
}

// ---- Consultas ----

async function traer() {
  try {
    const r = await fetch(`/presentador/eventos?desde=${estado.desde}`, { headers: { "X-Presentador": estado.llave }, cache: "no-store" });
    if (r.status === 403) { sinLlave(); return; }
    if (!r.ok) throw new Error(String(r.status));
    const datos = await r.json();
    estado.estrategias = datos.estrategias;
    estado.visible = datos.visible;
    for (const ev of datos.eventos) {
      aplicar(ev);
      estado.desde = Math.max(estado.desde, ev.n);
    }
    estado.fallos = 0;
    $("#proy-estado").textContent = "En vivo. Se actualiza cada segundo.";
  } catch {
    estado.fallos += 1;
    if (estado.fallos > 2) $("#proy-estado").textContent = "Sin conexión con el portátil. Reintentando…";
  }
  setTimeout(traer, 1000);
}

async function cifras() {
  try {
    const r = await fetch("/metricas/resumen", { cache: "no-store" });
    if (!r.ok) return;
    const c = await r.json();
    const filas = $("#cifras-filas");
    filas.replaceChildren();
    // En el mismo orden de las tarjetas: por frase, acumulada, híbrida
    const orden = [...estado.estrategias, ...Object.keys(c.por_estrategia).filter((e) => !estado.estrategias.includes(e))];
    for (const e of orden.filter((x) => c.por_estrategia[x])) {
      const v = c.por_estrategia[e];
      const tr = document.createElement("tr");
      const celdas = [
        nombre(e),
        `${v.llamadas_con_aviso} de ${c.llamadas}`,
        v.frase_media_del_aviso == null ? "—" : String(v.frase_media_del_aviso).replace(".", ","),
        String(v.falsas_alarmas),
      ];
      celdas.forEach((t, i) => {
        const celda = document.createElement(i === 0 ? "th" : "td");
        if (i === 0) celda.scope = "row";
        celda.textContent = t;
        tr.append(celda);
      });
      filas.append(tr);
    }
    const resp = c.respuesta_media_segundos == null ? "" : ` El servidor respondió en ${String(c.respuesta_media_segundos).replace(".", ",")} s en promedio.`;
    const llamadas = c.llamadas === 1 ? "1 llamada analizada" : `${c.llamadas} llamadas analizadas`;
    $("#cifras-nota").textContent = `${llamadas}, ${c.con_desenlace} con "¿Cómo terminó?".${resp}`;
  } catch { /* se intenta en la próxima vuelta */ }
}

async function descargar() {
  const r = await fetch("/metricas.csv", { headers: { "X-Presentador": estado.llave } });
  if (!r.ok) return;
  const url = URL.createObjectURL(await r.blob());
  const a = document.createElement("a");
  a.href = url;
  a.download = "centinela-cifras.csv";
  a.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

async function limpiar() {
  await fetch("/presentador/eventos", { method: "DELETE", headers: { "X-Presentador": estado.llave } }).catch(() => {});
  estado.llamadas.clear();
  $("#proy-llamadas").replaceChildren();
  $("#proy-vacio").classList.remove("oculto");
}

function sinLlave() {
  $("#proy-sin-llave").classList.remove("oculto");
  $("#proy-estado").textContent = "";
  document.querySelector(".proy-cuerpo").classList.add("oculto");
}

document.addEventListener("DOMContentLoaded", () => {
  estado.llave = leerLlave();
  if (!estado.llave) { sinLlave(); return; }
  $("#descargar").addEventListener("click", descargar);
  $("#limpiar").addEventListener("click", limpiar);
  traer();
  cifras();
  setInterval(cifras, 10000);
});
