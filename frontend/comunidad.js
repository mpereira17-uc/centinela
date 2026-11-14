"use strict";

// Tablero de la comunidad: totales de la semana que se actualizan solos, para que en la demostración
// se vea moverse cuando alguien reporta un número. Solo conteos; nada que identifique a nadie.

const $ = (s) => document.querySelector(s);
const CADA = 10_000;
let anterior = null;

function poner(id, valor) {
  const el = $(id);
  const antes = el.textContent;
  el.textContent = String(valor);
  // Un pulso cuando el número sube, para que se note desde lejos
  if (anterior && antes !== "–" && Number(valor) > Number(antes)) {
    const tarjeta = el.closest(".dato, .dato-principal");
    tarjeta.classList.remove("subio");
    void tarjeta.offsetWidth;
    tarjeta.classList.add("subio");
  }
}

function pintarModalidades(lista) {
  const ol = $("#modalidades");
  $("#sin-modalidades").classList.toggle("oculto", lista.length > 0);
  const maximo = Math.max(1, ...lista.map((m) => m.reportes));
  const filas = lista.map((m) => {
    const li = document.createElement("li");
    const nombre = document.createElement("span");
    nombre.className = "barra-nombre";
    nombre.textContent = m.nombre;
    const valor = document.createElement("span");
    valor.className = "barra-valor";
    valor.textContent = m.reportes === 1 ? "1 reporte" : `${m.reportes} reportes`;
    const pista = document.createElement("span");
    pista.className = "barra-pista";
    pista.setAttribute("aria-hidden", "true");
    const dato = document.createElement("span");
    dato.className = "barra-dato";
    dato.style.setProperty("--ancho", `${Math.round((m.reportes / maximo) * 100)}%`);
    pista.append(dato);
    li.append(nombre, valor, pista);
    return li;
  });
  ol.replaceChildren(...filas);
}

function pintar(t) {
  poner("#v-estafa", t.estafa);
  $("#v-numeros").textContent = t.numeros === 1 ? "De 1 número" : `De ${t.numeros} números distintos`;
  poner("#v-intento", t.intento);
  poner("#v-perdida", t.perdida);
  poner("#v-publicidad", t.publicidad);
  poner("#v-avisos", t.avisos.no_cayeron);
  pintarModalidades(t.modalidades);
  const ejemplo = $("#tablero-ejemplo");
  ejemplo.classList.toggle("oculto", !t.ejemplo);
  ejemplo.textContent = t.ejemplo
    ? `Incluye ${t.ejemplo} ${t.ejemplo === 1 ? "reporte" : "reportes"} de ejemplo de la demostración; los demás son reales.`
    : "";
  if (anterior && t.estafa > anterior.estafa) {
    const nuevos = t.estafa - anterior.estafa;
    $("#tablero-novedad").textContent = nuevos === 1 ? "Llegó un reporte nuevo." : `Llegaron ${nuevos} reportes nuevos.`;
  }
  anterior = t;
}

async function actualizar() {
  try {
    const r = await fetch("/comunidad/tablero", { cache: "no-store" });
    if (!r.ok) throw new Error();
    pintar(await r.json());
    $("#tablero-error").textContent = "";
    const hora = new Date().toLocaleTimeString("es-CO", { hour: "numeric", minute: "2-digit" });
    $("#tablero-hora").textContent = `En vivo · actualizado a las ${hora}`;
  } catch {
    $("#tablero-error").textContent = "No pudimos actualizar el tablero. Lo intentamos de nuevo en unos segundos.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  actualizar();
  setInterval(() => { if (!document.hidden) actualizar(); }, CADA);
  document.addEventListener("visibilitychange", () => { if (!document.hidden) actualizar(); });
});
