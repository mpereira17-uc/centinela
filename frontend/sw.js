"use strict";

// Service worker mínimo para que Centinela se pueda instalar como app.
// Guarda solo la interfaz (HTML, CSS, JS e íconos) para abrir rápido; nunca guarda respuestas de la API,
// porque llevan análisis de conversaciones y datos de la cuenta. Primero intenta la red, así siempre
// se ve la versión más reciente y la copia solo se usa sin conexión.

const VERSION = "centinela-v2";
const INTERFAZ = [
  "/", "/index.html", "/llamada.html", "/acompanante.html", "/practica.html", "/ayuda.html", "/cuenta.html", "/instalar.html",
  "/estilos.css", "/comun.js", "/app.js", "/llamada.js", "/acompanante.js", "/practica.js", "/ayuda.js", "/cuenta.js", "/instalar.js",
  "/manifest.webmanifest", "/iconos/icono-192.png", "/iconos/icono-512.png",
  "/buho/icono.svg", "/buho/tranquilo.svg", "/buho/atento.svg", "/buho/alerta.svg", "/buho/alarmado.svg",
];
const ES_INTERFAZ = /^\/($|[\w-]+\.(html|css|js|webmanifest)$|iconos\/|buho\/)/;

self.addEventListener("install", (ev) => {
  ev.waitUntil(caches.open(VERSION).then((c) => c.addAll(INTERFAZ)).then(() => self.skipWaiting()));
});

self.addEventListener("activate", (ev) => {
  ev.waitUntil(
    caches.keys()
      .then((claves) => Promise.all(claves.filter((k) => k !== VERSION).map((k) => caches.delete(k))))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (ev) => {
  const url = new URL(ev.request.url);
  if (ev.request.method !== "GET" || url.origin !== location.origin || !ES_INTERFAZ.test(url.pathname)) return;
  ev.respondWith(
    fetch(ev.request)
      .then((r) => {
        if (r.ok) {
          const copia = r.clone();
          caches.open(VERSION).then((c) => c.put(ev.request, copia));
        }
        return r;
      })
      .catch(() => caches.match(ev.request, { ignoreSearch: true })
        .then((r) => r || new Response("Sin conexión con Centinela.", { status: 503, headers: { "Content-Type": "text/plain; charset=utf-8" } }))),
  );
});
