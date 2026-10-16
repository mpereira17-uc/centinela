"use strict";

// Modo acompañante: Centinela escucha por el micrófono una llamada telefónica normal puesta en altavoz
// y analiza lo que oye por trozos de unos segundos. El audio no se guarda. Todo texto se inserta con textContent (A5).

const $ = (sel) => document.querySelector(sel);
const ETIQUETAS = { bajo: "Bajo", moderado: "Moderado", alto: "Alto", critico: "Crítico" };
const SEGUNDOS_POR_TROZO = 6;

const estado = {
  micro: null, llamadaId: null, numero: "", cola: Promise.resolve(), grabando: false, recorder: null,
  pantalla: null, terminada: false,
};

function error(texto) {
  $("#preparar-error").textContent = texto;
}

async function json(r) {
  const cuerpo = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(typeof cuerpo.detail === "string" ? cuerpo.detail : "Algo salió mal."), { status: r.status });
  return cuerpo;
}

// ---- Empezar ----

async function empezar() {
  error("");
  if (!$("#consentimiento").checked) { error("Marca la casilla de consentimiento para continuar."); $("#consentimiento").focus(); return; }
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder !== "function") {
    error("Este navegador no permite usar el micrófono. Prueba con Chrome o Safari actualizados.");
    return;
  }
  try {
    // Sin cancelación de eco ni supresión de ruido: la voz llega por el altavoz de otro celular
    // y esos filtros la tomarían como ruido de fondo
    estado.micro = await navigator.mediaDevices.getUserMedia({
      audio: { echoCancellation: false, noiseSuppression: false, autoGainControl: true },
    });
  } catch {
    error("Necesitamos permiso para usar el micrófono. Revísalo en los ajustes del navegador.");
    return;
  }
  try {
    await crearLlamada();
  } catch (e) {
    for (const p of estado.micro.getTracks()) p.stop();
    error(e instanceof TypeError ? "No pudimos conectar con Centinela." : e.message);
    return;
  }
  $("#preparar").classList.add("oculto");
  $("#en-llamada").classList.remove("oculto");
  $("#estado-llamada").textContent = "Escuchando. Deja este dispositivo cerca del altavoz.";
  $("#nivel").classList.add("escuchando"); // el búho pone cara de atento mientras escucha
  mantenerPantalla();
  escuchar(estado.micro);
  $("#colgar").focus();
}

async function crearLlamada() {
  const numero = $("#numero-llamada").value.trim();
  estado.numero = numero;
  let r = await fetch("/llamadas", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(numero ? { numero } : {}),
  });
  if (r.status === 422 && numero) {
    // Un número mal escrito no debe impedir escuchar
    estado.numero = "";
    r = await fetch("/llamadas", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
  }
  const llamada = await json(r);
  estado.llamadaId = llamada.id;
  mostrarNivel(null);
}

async function mantenerPantalla() {
  // Que la pantalla no se apague mientras escucha
  try {
    estado.pantalla = await navigator.wakeLock?.request("screen");
  } catch { /* sin bloqueo de pantalla; se sigue escuchando */ }
}

// ---- Escuchar por trozos ----

function encolar(tarea) {
  // Los trozos se analizan en orden, uno tras otro
  estado.cola = estado.cola.then(tarea).catch((e) => { $("#escucha").textContent = e.message; });
}

function escuchar(flujo) {
  estado.grabando = true;
  $("#escucha").textContent = "Centinela analiza lo que oye por partes de unos segundos.";
  const tipo = ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"].find((t) => MediaRecorder.isTypeSupported(t)) || "";

  // Se graba por trozos completos (parar y volver a empezar) para que cada uno sea un archivo válido
  const grabarTrozo = () => {
    if (!estado.grabando) return;
    const partes = [];
    const recorder = new MediaRecorder(flujo, tipo ? { mimeType: tipo } : undefined);
    estado.recorder = recorder;
    recorder.addEventListener("dataavailable", (e) => { if (e.data.size) partes.push(e.data); });
    recorder.addEventListener("stop", () => {
      const audio = new Blob(partes, { type: recorder.mimeType || "audio/webm" });
      if (audio.size > 2000) encolar(() => analizarAudio(audio));
      grabarTrozo();
    });
    recorder.start();
    setTimeout(() => { if (recorder.state === "recording") recorder.stop(); }, SEGUNDOS_POR_TROZO * 1000);
  };
  grabarTrozo();
}

async function analizarAudio(audio) {
  if (!estado.grabando) return;
  const datos = new FormData();
  datos.append("audio", audio, audio.type.includes("mp4") ? "trozo.mp4" : "trozo.webm");
  datos.append("consentimiento", "true");
  datos.append("hablante", "altavoz");
  const r = await fetch(`/llamadas/${estado.llamadaId}/audio`, { method: "POST", body: datos });
  if (r.status === 503) {
    detener();
    $("#escucha").textContent = "La transcripción de voz no está instalada en el servidor de Centinela, así que no puede escuchar.";
    return;
  }
  if (r.status === 422) return; // trozo sin voz entendible
  const resultado = await json(r);
  for (const item of resultado.resultados) mostrarResultado(item);
}

function detener() {
  estado.grabando = false;
  if (estado.recorder && estado.recorder.state === "recording") estado.recorder.stop();
  if (estado.micro) for (const p of estado.micro.getTracks()) p.stop();
  estado.pantalla?.release().catch(() => {});
}

// ---- Mostrar lo que se oyó ----

function mostrarResultado(r) {
  const d = r.decision_visible;
  const li = document.createElement("li");
  li.className = "frase";
  li.dataset.nivel = d.nivel;
  li.dataset.hablante = "llamante";
  const texto = document.createElement("p");
  texto.className = "frase-texto";
  texto.textContent = r.fragmento.texto;
  const nivel = document.createElement("span");
  nivel.className = "frase-nivel";
  const icono = document.createElement("span");
  icono.className = "nivel-icono";
  icono.setAttribute("aria-hidden", "true");
  const etiqueta = document.createElement("span");
  etiqueta.textContent = `Riesgo ${ETIQUETAS[d.nivel].toLowerCase()}`;
  nivel.append(icono, etiqueta);
  li.append(texto, nivel);
  $("#conversacion").append(li);
  $("#dicho-vacio").classList.add("oculto");
  mostrarNivel(d);
  if (r.mostrar_aviso) mostrarAlerta(d);
}

function mostrarNivel(d) {
  const caja = $("#nivel");
  caja.classList.toggle("sin-datos", !d);
  caja.dataset.nivel = d ? d.nivel : "bajo";
  $("#nivel-valor").textContent = d ? ETIQUETAS[d.nivel] : "Sin analizar";
  $("#nivel-mensaje").textContent = d ? d.mensaje : "";
}

function mostrarAlerta(d) {
  // El servidor marca el aviso una sola vez por llamada
  const alerta = $("#alerta");
  const [titulo, ...resto] = d.mensaje.split(". ");
  alerta.dataset.nivel = d.nivel;
  alerta.querySelector(".alerta-titulo").textContent = titulo;
  alerta.querySelector(".alerta-texto").textContent = resto.join(". ");
  window.Centinela?.completarAviso(alerta, d, resto[0]);
  alerta.classList.remove("oculto");
  alerta.focus();
}

// ---- Terminar ----

function terminar() {
  if (estado.terminada) return;
  estado.terminada = true;
  detener();
  $("#estado-llamada").textContent = "Centinela dejó de escuchar.";
  $("#nivel").classList.remove("escuchando");
  $("#colgar").classList.add("oculto");
  const otra = document.createElement("a");
  otra.href = "/acompanante.html";
  otra.textContent = "Escuchar otra llamada";
  $("#compartir").replaceChildren(otra);
  $("#desenlace").classList.remove("oculto");
  $("#desenlace").scrollIntoView({ block: "start" });
}

// ---- ¿Cómo terminó? (un toque al terminar) ----

const GRACIAS = {
  perdida: "Lo sentimos mucho. Te mostramos qué hacer ahora, en orden.",
  intento: "Gracias. Bien hecho al no caer.",
  publicidad: "Gracias. La publicidad se cuenta aparte de las estafas.",
  legitima: "Gracias. Esto nos ayuda a no alarmar por llamadas normales.",
};

async function contarDesenlace(resultado) {
  const botones = document.querySelectorAll("#desenlace button");
  botones.forEach((b) => { b.disabled = true; b.classList.toggle("elegido", b.dataset.resultado === resultado); });
  const salida = $("#desenlace-estado");
  try {
    await json(await fetch(`/llamadas/${estado.llamadaId}/desenlace`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ resultado }),
    }));
    salida.replaceChildren(GRACIAS[resultado]);
    if (estado.numero) await reportarNumero(resultado, salida);
    if (resultado === "perdida") {
      const guia = document.createElement("a");
      guia.href = "/ayuda.html#me-estafaron";
      guia.className = "boton-principal";
      guia.textContent = "Ver qué hacer ahora";
      salida.append(" ", guia);
    }
  } catch (e) {
    botones.forEach((b) => { b.disabled = false; });
    salida.textContent = e instanceof TypeError ? "No pudimos conectar con Centinela." : e.message;
  }
}

async function reportarNumero(resultado, salida) {
  // El reporte va respaldado por el análisis de esta llamada; la categoría sale de lo detectado
  const r = await fetch("/reportes", {
    method: "POST",
    headers: { "Content-Type": "application/json", "X-Centinela": "1" },
    body: JSON.stringify({ numero: estado.numero, resultado, llamada_id: estado.llamadaId }),
  });
  if (r.ok) {
    const datos = await r.json();
    salida.append(` También quedó como reporte del número${datos.respaldado ? ", respaldado por este análisis" : ""}.`);
  } else if (r.status === 401) {
    const entrar = document.createElement("a");
    entrar.href = "/cuenta.html";
    entrar.textContent = "Entra a tu cuenta";
    salida.append(" ", entrar, " para que tu respuesta también cuente como reporte del número.");
  } else if (r.status === 409) {
    salida.append(" Ya habías reportado este número.");
  }
}

document.addEventListener("DOMContentLoaded", () => {
  $("#empezar").addEventListener("click", empezar);
  $("#colgar").addEventListener("click", terminar);
  $("#cerrar-alerta").addEventListener("click", () => $("#alerta").classList.add("oculto"));
  document.querySelectorAll("#desenlace [data-resultado]").forEach((b) => b.addEventListener("click", () => contarDesenlace(b.dataset.resultado)));
  // Al volver a la app, el bloqueo de pantalla se pierde y se pide de nuevo
  document.addEventListener("visibilitychange", () => {
    if (document.visibilityState === "visible" && estado.grabando) mantenerPantalla();
  });
});
