"use strict";

// Página para instalar Centinela como app desde el navegador (PWA), con el código QR para pasarla.

const $ = (sel) => document.querySelector(sel);
let solicitud = null;

function yaInstalada() {
  return matchMedia("(display-mode: standalone)").matches || navigator.standalone === true;
}

function mostrarPasos() {
  const iphone = /iphone|ipad|ipod/i.test(navigator.userAgent);
  $(iphone ? "#pasos-iphone" : "#pasos-android").classList.remove("oculto");
}

document.addEventListener("DOMContentLoaded", () => {
  $("#direccion").textContent = location.origin;
  if (yaInstalada()) {
    $("#instalar-estado").textContent = "Centinela ya está instalada en este celular.";
    return;
  }
  // Chrome avisa cuando la app se puede instalar con un toque; si no avisa, se muestran los pasos a mano
  const respaldo = setTimeout(mostrarPasos, 2500);
  window.addEventListener("beforeinstallprompt", (ev) => {
    ev.preventDefault();
    clearTimeout(respaldo);
    solicitud = ev;
    $("#instalar-app").classList.remove("oculto");
  });
  $("#instalar-app").addEventListener("click", async () => {
    if (!solicitud) return;
    solicitud.prompt();
    const { outcome } = await solicitud.userChoice;
    solicitud = null;
    $("#instalar-app").classList.add("oculto");
    $("#instalar-estado").textContent = outcome === "accepted" ? "Listo. Busca el ícono de Centinela en tu pantalla de inicio." : "No pasa nada, puedes usarla sin instalar.";
  });
  window.addEventListener("appinstalled", () => {
    $("#instalar-estado").textContent = "Listo. Busca el ícono de Centinela en tu pantalla de inicio.";
  });
});
