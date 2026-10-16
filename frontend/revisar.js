"use strict";

// Revisión previa a la demostración, en el mismo celular y la misma red que se van a usar.
// Prueba de verdad lo que puede fallar en vivo: que el TURN responda desde esta red, que la voz esté
// cargada en el portátil y que el micrófono oiga. Nada de lo que oye el micrófono sale del celular.
// Todo texto se inserta con textContent (A5).

const $ = (sel) => document.querySelector(sel);

function marcar(id, estado, texto) {
  const fila = $(`#${id}`);
  fila.dataset.estado = estado;
  fila.querySelector(".ayuda").textContent = texto;
}

async function pedir(ruta) {
  const r = await fetch(ruta, { cache: "no-store" });
  if (!r.ok) throw new Error(String(r.status));
  return r.json();
}

// ---- Servidor ----

async function revisarServidor() {
  const inicio = performance.now();
  try {
    await pedir("/salud");
    const ms = Math.round(performance.now() - inicio);
    if (ms > 1500) marcar("r-servidor", "regular", `Responde, pero lento (${ms} ms). Revisa la señal de este celular o la red del portátil.`);
    else marcar("r-servidor", "bien", `Responde en ${ms} ms.`);
    return true;
  } catch {
    marcar("r-servidor", "mal", "No responde. Revisa que el portátil siga con python sustentacion.py abierto y que la dirección sea la de hoy.");
    return false;
  }
}

// ---- Voz ----

let vigiaVoz = null;

async function revisarVoz() {
  clearTimeout(vigiaVoz);
  let v;
  try {
    v = await pedir("/transcripcion/estado");
  } catch {
    marcar("r-voz", "mal", "No se pudo preguntar por la voz.");
    return;
  }
  if (v.estado === "lista") {
    const s = v.ultima_segundos;
    if (s != null && s > 3) {
      marcar("r-voz", "regular", `Lista, pero cada frase tarda ${s} s en el portátil. El aviso puede llegar tarde: mira el plan B de la guía.`);
    } else {
      marcar("r-voz", "bien", s != null ? `Lista. La última frase tardó ${s} s.` : `Lista (modelo ${v.modelo}).`);
    }
  } else if (v.estado === "cargando") {
    marcar("r-voz", "revisando", "Cargando el modelo de voz en el portátil…");
    vigiaVoz = setTimeout(revisarVoz, 3000);
  } else if (v.estado === "no_disponible") {
    marcar("r-voz", "mal", `No disponible: ${v.detalle || "falta instalar la transcripción en el portátil."} Sin voz, usa el modo texto de la llamada.`);
  } else {
    marcar("r-voz", "regular", "Se cargará con la primera frase, que tardará unos segundos más. Con python sustentacion.py se carga al arrancar.");
  }
}

// ---- Red: ¿conecta entre redes distintas desde aquí? ----

function tipoDeCandidato(c) {
  if (c.type) return c.type;
  const m = /\btyp (\w+)/.exec(c.candidate || "");
  return m ? m[1] : "";
}

async function revisarRed() {
  if (typeof RTCPeerConnection !== "function") {
    marcar("r-red", "mal", "Este navegador no permite llamadas por internet. Usa Chrome o Safari actualizados.");
    return;
  }
  let ice;
  try {
    ice = await pedir("/webrtc/ice");
  } catch {
    marcar("r-red", "mal", "No se pudo preguntar por los servidores de la llamada.");
    return;
  }
  // Se abre una conexión de prueba sin audio, solo para ver qué caminos encuentra desde esta red
  const pc = new RTCPeerConnection({ iceServers: ice.iceServers || [] });
  const tipos = new Set();
  const listo = new Promise((resolver) => {
    const fin = setTimeout(resolver, 8000);
    pc.addEventListener("icecandidate", (ev) => {
      if (ev.candidate) tipos.add(tipoDeCandidato(ev.candidate));
      else { clearTimeout(fin); resolver(); }
    });
  });
  try {
    pc.createDataChannel("revision");
    await pc.setLocalDescription(await pc.createOffer());
    await listo;
  } finally {
    pc.close();
  }

  if (tipos.has("relay")) {
    marcar("r-red", "bien", "Lista: el TURN responde desde esta red, así que conecta aunque el otro celular esté en datos o en otro Wi‑Fi.");
  } else if (ice.entre_redes) {
    marcar("r-red", "mal", "El TURN está configurado pero no responde desde esta red. Prueba con otra red o revisa sus claves en el portátil.");
  } else if (tipos.has("srflx")) {
    marcar("r-red", "regular", "Sin TURN: entre redes distintas conecta solo a veces (entre datos móviles y Wi‑Fi suele fallar). Pon las claves del TURN o usa los dos celulares en la misma red.");
  } else {
    marcar("r-red", "regular", "Solo conecta si los dos celulares están en la misma red Wi‑Fi. Para otras redes, pon las claves del TURN.");
  }
}

// ---- Pantalla ----

function revisarPantalla() {
  if (window.CentinelaApp) marcar("r-pantalla", "bien", "La app la mantiene encendida mientras el modo acompañante escucha.");
  else if ("wakeLock" in navigator) marcar("r-pantalla", "bien", "El navegador la mantiene encendida mientras el modo acompañante escucha.");
  else marcar("r-pantalla", "regular", "Este navegador no puede mantenerla encendida. Sube el tiempo de apagado de la pantalla del celular a 2 minutos o más.");
}

// ---- Micrófono ----

async function probarMicro() {
  const boton = $("#probar-micro");
  boton.disabled = true;
  if (!window.CentinelaEscucha?.disponible() || !navigator.mediaDevices?.getUserMedia) {
    marcar("r-micro", "mal", "Este navegador no permite grabar audio. Usa Chrome o Safari actualizados.");
    boton.disabled = false;
    return;
  }
  let flujo;
  try {
    // Los mismos ajustes del modo acompañante, para probar lo mismo que se usará
    flujo = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: true } });
  } catch {
    marcar("r-micro", "mal", "No hay permiso para el micrófono. Revísalo en los ajustes del navegador o de la app.");
    boton.disabled = false;
    return;
  }
  marcar("r-micro", "revisando", "Habla o pon cerca un celular en altavoz durante unos segundos…");
  const medidor = $("#medidor");
  medidor.classList.remove("oculto");
  let oyo = false;
  let ctx;
  try {
    ctx = new (window.AudioContext || window.webkitAudioContext)();
    await ctx.resume?.();
    const analizador = ctx.createAnalyser();
    analizador.fftSize = 1024;
    ctx.createMediaStreamSource(flujo).connect(analizador);
    const muestras = new Float32Array(analizador.fftSize);
    const fin = performance.now() + 6000;
    await new Promise((resolver) => {
      const t = setInterval(() => {
        analizador.getFloatTimeDomainData(muestras);
        let suma = 0;
        for (const m of muestras) suma += m * m;
        const rms = Math.sqrt(suma / muestras.length);
        medidor.style.setProperty("--volumen", Math.min(1, rms / 0.15).toFixed(2));
        if (rms > 0.03) { oyo = true; medidor.classList.add("voz"); }
        if (performance.now() > fin) { clearInterval(t); resolver(); }
      }, 50);
    });
  } catch {
    // Sin medición de volumen: el modo acompañante usará trozos fijos
  } finally {
    for (const p of flujo.getTracks()) p.stop();
    ctx?.close().catch(() => {});
    boton.disabled = false;
  }
  if (oyo) marcar("r-micro", "bien", "Te oye bien.");
  else if (!ctx) marcar("r-micro", "regular", "El micrófono abrió, pero no se pudo medir el volumen en este navegador.");
  else marcar("r-micro", "regular", "Se oyó muy bajo. Acércalo al altavoz o sube el volumen de la llamada.");
}

// ---- Todo ----

async function revisarTodo() {
  for (const id of ["r-servidor", "r-voz", "r-red", "r-pantalla"]) marcar(id, "revisando", "Revisando…");
  revisarPantalla();
  if (!(await revisarServidor())) {
    marcar("r-voz", "mal", "Sin conexión con Centinela.");
    marcar("r-red", "mal", "Sin conexión con Centinela.");
    return;
  }
  await Promise.all([revisarVoz(), revisarRed().catch(() => marcar("r-red", "mal", "No se pudo probar la conexión de la llamada."))]);
}

document.addEventListener("DOMContentLoaded", () => {
  $("#probar-micro").addEventListener("click", probarMicro);
  $("#otra-vez").addEventListener("click", revisarTodo);
  revisarTodo();
});
