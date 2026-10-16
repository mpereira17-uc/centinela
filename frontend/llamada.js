"use strict";

// Llamada simulada por WebRTC. El servidor solo reenvía los mensajes de conexión;
// el audio va directo entre navegadores. Todo texto se inserta con textContent (A5).

const $ = (sel) => document.querySelector(sel);
const ETIQUETAS = { bajo: "Bajo", moderado: "Moderado", alto: "Alto", critico: "Crítico" };
const SEGUNDOS_POR_TROZO = 6;

const estado = {
  rol: null, codigo: null, ws: null, pc: null, micro: null, llamadaId: null,
  inicio: 0, ultimoFin: 0, cola: Promise.resolve(), grabando: false, recorder: null,
  pendientes: [], terminada: false, ice: [],
};

function rolElegido() {
  return document.querySelector('input[name="rol"]:checked').value;
}

function error(texto) {
  $("#preparar-error").textContent = texto;
}

function estadoLlamada(texto) {
  $("#estado-llamada").textContent = texto;
}

async function json(r) {
  const cuerpo = await r.json().catch(() => ({}));
  if (!r.ok) throw Object.assign(new Error(typeof cuerpo.detail === "string" ? cuerpo.detail : "Algo salió mal."), { status: r.status });
  return cuerpo;
}

// ---- Preparar ----

async function crear() {
  error("");
  if (!$("#consentimiento").checked) { error("Marca la casilla de consentimiento para continuar."); $("#consentimiento").focus(); return; }
  try {
    const { codigo } = await json(await fetch("/salas", { method: "POST" }));
    await conectar(codigo, rolElegido(), true);
  } catch (e) {
    error(e instanceof TypeError ? "No pudimos conectar con Centinela." : e.message);
  }
}

async function unirse(ev) {
  ev.preventDefault();
  error("");
  const codigo = $("#codigo").value.trim();
  if (!codigo) { error("Escribe el código que te compartieron."); $("#codigo").focus(); return; }
  if (!$("#consentimiento").checked) { error("Marca la casilla de consentimiento para continuar."); $("#consentimiento").focus(); return; }
  try {
    const sala = await json(await fetch(`/salas/${encodeURIComponent(codigo)}`));
    if (!sala.roles_libres.length) { error("Esa llamada ya tiene a sus dos personas."); return; }
    // Si el papel elegido ya está ocupado, se toma el que queda
    const rol = sala.roles_libres.includes(rolElegido()) ? rolElegido() : sala.roles_libres[0];
    await conectar(sala.codigo, rol, false);
  } catch (e) {
    error(e instanceof TypeError ? "No pudimos conectar con Centinela." : e.message);
  }
}

async function conectar(codigo, rol, creador) {
  estado.codigo = codigo;
  estado.rol = rol;
  try {
    estado.micro = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    estado.micro = null;
  }
  estado.ice = await servidoresIce();

  const protocolo = location.protocol === "https:" ? "wss" : "ws";
  const ws = new WebSocket(`${protocolo}://${location.host}/salas/${encodeURIComponent(codigo)}/ws?rol=${rol}`);
  estado.ws = ws;
  ws.addEventListener("open", () => ws.send(JSON.stringify({ tipo: "unirse", consentimiento: true })));
  ws.addEventListener("message", (ev) => alRecibir(JSON.parse(ev.data)).catch(() => {}));
  ws.addEventListener("close", (ev) => {
    const motivos = {
      4401: "Falta el consentimiento.", 4404: "Esa llamada ya no existe.", 4409: "Ese papel ya lo tiene otra persona.",
      4403: "No se pudo abrir la conexión desde esta página.", 4413: "Se enviaron demasiados datos.",
    };
    if (motivos[ev.code]) {
      if ($("#en-llamada").classList.contains("oculto")) error(motivos[ev.code]);
      else terminar(motivos[ev.code]);
    } else if (!estado.terminada && !$("#en-llamada").classList.contains("oculto")) {
      terminar("Se perdió la conexión con Centinela.");
    }
  });

  $("#codigo-sala").textContent = codigo;
  $("#compartir").textContent = creador
    ? `Comparte este código con la otra persona: ${codigo}. Debe abrir esta misma página en otro navegador y elegir "Unirme".`
    : "";
}

function mostrarLlamada() {
  $("#preparar").classList.add("oculto");
  $("#en-llamada").classList.remove("oculto");
  $(estado.rol === "llama" ? "#vista-llama" : "#vista-recibe").classList.remove("oculto");
  estadoLlamada(estado.micro
    ? "Esperando a la otra persona…"
    : "Esperando a la otra persona… No pudimos usar tu micrófono, pero puedes seguir en modo texto.");
  $("#colgar").focus();
}

// ---- Señalización y WebRTC ----

function enviar(mensaje) {
  if (estado.ws && estado.ws.readyState === WebSocket.OPEN) estado.ws.send(JSON.stringify(mensaje));
}

async function servidoresIce() {
  // Con STUN y TURN configurados en el servidor, la llamada conecta entre redes distintas
  // (datos móviles, otro Wi-Fi). Sin ellos, solo en el mismo equipo o la misma red.
  try {
    const r = await fetch("/webrtc/ice");
    return r.ok ? (await r.json()).iceServers : [];
  } catch {
    return [];
  }
}

function prepararConexion() {
  if (estado.pc) return estado.pc;
  const pc = new RTCPeerConnection({ iceServers: estado.ice });
  estado.pc = pc;
  if (estado.micro) {
    for (const pista of estado.micro.getAudioTracks()) pc.addTrack(pista, estado.micro);
  } else {
    pc.addTransceiver("audio", { direction: "recvonly" });
  }
  pc.addEventListener("icecandidate", (ev) => { if (ev.candidate) enviar({ tipo: "candidato", candidato: ev.candidate.toJSON() }); });
  pc.addEventListener("track", (ev) => {
    const flujo = ev.streams[0] || new MediaStream([ev.track]);
    $("#audio-remoto").srcObject = flujo;
    if (estado.rol === "recibe") empezarAEscuchar(flujo);
  });
  pc.addEventListener("connectionstatechange", () => {
    const textos = {
      connecting: "Conectando el audio…", connected: "En llamada.",
      disconnected: "La conexión se interrumpió. Intentando recuperarla…", failed: "No se pudo conectar el audio. Pueden seguir en modo texto.",
    };
    if (textos[pc.connectionState] && !estado.terminada) estadoLlamada(textos[pc.connectionState]);
  });
  return pc;
}

async function aplicarCandidatos() {
  for (const c of estado.pendientes.splice(0)) await estado.pc.addIceCandidate(c).catch(() => {});
}

async function alRecibir(m) {
  switch (m.tipo) {
    case "unido":
      mostrarLlamada();
      break;
    case "listos": {
      estadoLlamada("La otra persona se unió. Conectando…");
      $("#compartir").textContent = "";
      const pc = prepararConexion();
      if (estado.rol === "recibe") await empezarAnalisis();
      if (estado.rol === "llama") {
        await pc.setLocalDescription(await pc.createOffer());
        enviar({ tipo: "oferta", sdp: pc.localDescription.sdp });
      }
      break;
    }
    case "oferta": {
      const pc = prepararConexion();
      await pc.setRemoteDescription({ type: "offer", sdp: String(m.sdp) });
      await aplicarCandidatos();
      await pc.setLocalDescription(await pc.createAnswer());
      enviar({ tipo: "respuesta", sdp: pc.localDescription.sdp });
      break;
    }
    case "respuesta":
      await estado.pc.setRemoteDescription({ type: "answer", sdp: String(m.sdp) });
      await aplicarCandidatos();
      break;
    case "candidato":
      if (estado.pc && estado.pc.remoteDescription) await estado.pc.addIceCandidate(m.candidato).catch(() => {});
      else estado.pendientes.push(m.candidato);
      break;
    case "texto":
      if (estado.rol === "recibe" && typeof m.texto === "string") {
        const texto = m.texto.trim().slice(0, 2000);
        if (texto) encolar(() => analizarTexto(texto));
      }
      break;
    case "colgar":
    case "colgo":
      terminar("La otra persona colgó.");
      break;
  }
}

// ---- Análisis (solo quien recibe) ----

async function empezarAnalisis() {
  const numero = $("#numero-llamada").value.trim();
  estado.numero = numero;
  const cuerpo = JSON.stringify(numero ? { numero } : {});
  let r = await fetch("/llamadas", { method: "POST", headers: { "Content-Type": "application/json" }, body: cuerpo });
  if (r.status === 422 && numero) {
    // Un número mal escrito no debe impedir la llamada de prueba
    estado.numero = "";
    r = await fetch("/llamadas", { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
  }
  const llamada = await json(r);
  estado.llamadaId = llamada.id;
  estado.inicio = performance.now();
  mostrarNivel(null);
}

function encolar(tarea) {
  // Las frases se analizan en orden, una tras otra
  estado.cola = estado.cola.then(tarea).catch((e) => { $("#escucha").textContent = e.message; });
}

async function analizarTexto(texto) {
  const fin = Math.max(estado.ultimoFin, (performance.now() - estado.inicio) / 1000);
  const r = await fetch(`/llamadas/${estado.llamadaId}/fragmentos`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ texto, hablante: "llamante", inicio: estado.ultimoFin, fin }),
  });
  const resultado = await json(r);
  estado.ultimoFin = fin;
  mostrarResultado(resultado);
}

function empezarAEscuchar(flujo) {
  if (estado.grabando || typeof MediaRecorder !== "function") return;
  estado.grabando = true;
  $("#escucha").textContent = "Escuchando a quien llama. Centinela analiza su voz por partes de unos segundos.";
  const tipo = ["audio/webm;codecs=opus", "audio/webm", "audio/ogg"].find((t) => MediaRecorder.isTypeSupported(t)) || "";

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
  datos.append("audio", audio, "trozo.webm");
  datos.append("consentimiento", "true");
  datos.append("hablante", "llamante");
  const r = await fetch(`/llamadas/${estado.llamadaId}/audio`, { method: "POST", body: datos });
  if (r.status === 503) {
    detenerEscucha();
    $("#escucha").textContent = "La transcripción de voz no está instalada en este equipo, así que Centinela no puede analizar la voz. Quien llama puede escribir sus frases.";
    return;
  }
  if (r.status === 422) return; // trozo sin voz entendible
  const resultado = await json(r);
  for (const item of resultado.resultados) mostrarResultado(item);
}

function detenerEscucha() {
  estado.grabando = false;
  if (estado.recorder && estado.recorder.state === "recording") estado.recorder.stop();
}

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

// ---- Quien llama: modo texto ----

function enviarFrase(ev) {
  ev.preventDefault();
  const texto = $("#frase").value.trim();
  if (!texto) { $("#frase").focus(); return; }
  enviar({ tipo: "texto", texto });
  const li = document.createElement("li");
  li.className = "frase";
  li.dataset.hablante = "propio";
  const p = document.createElement("p");
  p.className = "frase-texto";
  p.textContent = texto;
  li.append(p);
  $("#enviadas").append(li);
  $("#frase").value = "";
  $("#frase").focus();
}

// ---- Colgar ----

function terminar(motivo) {
  if (estado.terminada) return;
  estado.terminada = true;
  detenerEscucha();
  if (estado.pc) estado.pc.close();
  if (estado.micro) for (const p of estado.micro.getTracks()) p.stop();
  if (estado.ws && estado.ws.readyState === WebSocket.OPEN) estado.ws.close();
  estadoLlamada(`${motivo} La llamada terminó.`);
  $("#colgar").classList.add("oculto");
  $("#form-texto").classList.add("oculto");
  const otra = document.createElement("a");
  otra.href = "/llamada.html";
  otra.textContent = "Hacer otra llamada de prueba";
  $("#compartir").replaceChildren(otra);
  if (estado.rol === "recibe" && estado.llamadaId) {
    $("#desenlace").classList.remove("oculto");
    $("#desenlace").scrollIntoView({ block: "start" });
  }
}

// ---- ¿Cómo terminó? (un toque al colgar) ----

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

async function avisarRed() {
  try {
    const { entre_redes } = await json(await fetch("/webrtc/ice"));
    if (entre_redes) $("#aviso-red").textContent = "Funciona con datos móviles o con cualquier Wi-Fi.";
  } catch { /* se queda el aviso de la misma red */ }
}

document.addEventListener("DOMContentLoaded", () => {
  avisarRed();
  $("#crear").addEventListener("click", crear);
  $("#form-unirse").addEventListener("submit", unirse);
  $("#form-texto").addEventListener("submit", enviarFrase);
  $("#colgar").addEventListener("click", () => { enviar({ tipo: "colgar" }); terminar("Colgaste."); });
  // "Cuelgo y verifico" en el aviso crítico cuelga de verdad esta llamada
  $("#alerta").addEventListener("centinela:decision", (e) => {
    if (e.detail === "cuelgo" && !estado.terminada) { enviar({ tipo: "colgar" }); terminar("Colgaste por el aviso de Centinela."); }
  });
  $("#cerrar-alerta").addEventListener("click", () => $("#alerta").classList.add("oculto"));
  document.querySelectorAll("#desenlace [data-resultado]").forEach((b) => b.addEventListener("click", () => contarDesenlace(b.dataset.resultado)));
  document.querySelectorAll('input[name="rol"]').forEach((r) => r.addEventListener("change", () => {
    $("#caja-numero-llamada").classList.toggle("oculto", rolElegido() !== "recibe");
  }));
  const codigo = new URLSearchParams(location.search).get("codigo");
  if (codigo) $("#codigo").value = codigo.slice(0, 12);
});
