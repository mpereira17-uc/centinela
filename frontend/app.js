"use strict";

// Todo el texto del usuario se inserta con textContent, nunca como HTML (modelo de amenazas, A5).

const ETIQUETAS = { bajo: "Bajo", moderado: "Moderado", alto: "Alto", critico: "Crítico" };
const HABLANTES = { llamante: "La persona que llama", usuario: "Yo", audio: "Del audio" };

const EJEMPLOS = {
  estafa: [
    ["llamante", "Buenas tardes, le hablamos del área de seguridad del banco."],
    ["usuario", "Sí, ¿qué pasó?"],
    ["llamante", "Detectamos un movimiento extraño y su cuenta va a quedar bloqueada."],
    ["llamante", "Para evitarlo necesito que me dicte el código que le acaba de llegar por mensaje."],
    ["llamante", "Es urgente y no cuelgue, por favor."],
  ],
  legitima: [
    ["llamante", "Hola, te habla Laura de la tienda, tu pedido ya está listo."],
    ["usuario", "Qué bien, ¿hasta qué hora puedo pasar?"],
    ["llamante", "Hasta las siete. Recuerda que nunca te pediremos claves ni códigos por teléfono."],
  ],
};

const $ = (sel) => document.querySelector(sel);
const estado = { llamadaId: null, inicio: 0, ultimoFin: 0, ocupado: false };

async function api(ruta, opciones = {}) {
  let r;
  try {
    r = await fetch(ruta, { headers: { "Content-Type": "application/json" }, ...opciones });
  } catch {
    throw new Error("No pudimos conectar con Centinela. Revisa que el servidor esté encendido.");
  }
  if (!r.ok) {
    const error = new Error(mensajeDeError(r.status));
    error.status = r.status;
    throw error;
  }
  return r.json();
}

function mensajeDeError(status) {
  switch (status) {
    case 404: return "La conversación ya no existe en el servidor. Empezamos una nueva.";
    case 413: return "Esta conversación llegó al máximo de frases. Empieza una nueva.";
    case 422: return "La frase está vacía o es demasiado larga (máximo 2000 caracteres).";
    case 429: return "El servidor está ocupado. Intenta de nuevo en un momento.";
    default: return "Algo salió mal al analizar la frase. Intenta de nuevo.";
  }
}

function mostrarGuardado(guardada) {
  $("#guardado").textContent = guardada
    ? "Esta conversación se guarda en tu historial. Puedes verla o borrarla en Mi cuenta."
    : "Esta conversación no se guarda.";
}

async function nuevaConversacion() {
  const numero = $("#numero").value.trim();
  let llamada;
  try {
    llamada = await api("/llamadas", { method: "POST", body: JSON.stringify(numero ? { numero } : {}) });
  } catch (e) {
    if (e.status === 422) throw new Error("Revisa el número que te llama, o déjalo vacío. Ejemplo: 300 123 4567.");
    throw e;
  }
  estado.llamadaId = llamada.id;
  estado.numeroAplicado = numero;
  mostrarGuardado(llamada.guardada);
  $("#numero-aviso").textContent = "";
  estado.inicio = performance.now();
  estado.ultimoFin = 0;
  $("#conversacion").replaceChildren();
  $("#conv-vacia").classList.remove("oculto");
  $("#alerta").classList.add("oculto");
  mostrarNivel(null);
}

async function enviarFrase(texto, hablante) {
  // Marcas de tiempo relativas al inicio de la conversación, en segundos
  const fin = Math.max(estado.ultimoFin, (performance.now() - estado.inicio) / 1000);
  const cuerpo = JSON.stringify({ texto, hablante, inicio: estado.ultimoFin, fin });
  if (!estado.llamadaId) await nuevaConversacion();
  try {
    const r = await api(`/llamadas/${estado.llamadaId}/fragmentos`, { method: "POST", body: cuerpo });
    estado.ultimoFin = fin;
    return r;
  } catch (e) {
    if (e.status !== 404) throw e;
    // El servidor se reinició y perdió la conversación: se crea otra y se reintenta una vez
    await nuevaConversacion();
    mostrarError(e.message);
    return api(`/llamadas/${estado.llamadaId}/fragmentos`, { method: "POST", body: cuerpo });
  }
}

function mostrarNivel(decision) {
  const caja = $("#nivel");
  if (!decision) {
    caja.classList.add("sin-datos");
    caja.dataset.nivel = "bajo";
    $("#nivel-valor").textContent = "Sin analizar";
    $("#nivel-mensaje").textContent = "Agrega la primera frase para empezar.";
    return;
  }
  caja.classList.remove("sin-datos");
  caja.dataset.nivel = decision.nivel;
  $("#nivel-valor").textContent = ETIQUETAS[decision.nivel];
  $("#nivel-mensaje").textContent = decision.mensaje;
}

function mostrarAlerta(decision) {
  const alerta = $("#alerta");
  const [titulo, ...resto] = decision.mensaje.split(". ");
  alerta.dataset.nivel = decision.nivel;
  alerta.querySelector(".alerta-titulo").textContent = titulo;
  alerta.querySelector(".alerta-texto").textContent = resto.join(". ");
  window.Centinela?.completarAviso(alerta, decision, resto[0]);
  alerta.classList.remove("oculto");
  alerta.focus();
}

function agregarFrase(texto, hablante, respuesta) {
  const visible = respuesta.decision_visible;
  const li = document.createElement("li");
  li.className = "frase";
  li.dataset.nivel = visible.nivel;
  li.dataset.hablante = hablante;

  const quien = document.createElement("p");
  quien.className = "frase-quien";
  quien.textContent = HABLANTES[hablante];

  const p = document.createElement("p");
  p.className = "frase-texto";
  p.textContent = texto;

  const nivel = document.createElement("span");
  nivel.className = "frase-nivel";
  const icono = document.createElement("span");
  icono.className = "nivel-icono";
  icono.setAttribute("aria-hidden", "true");
  nivel.append(icono, `Riesgo ${ETIQUETAS[visible.nivel].toLowerCase()}`);

  li.append(quien, p, nivel);

  if (visible.senales.length) {
    const det = document.createElement("details");
    const sum = document.createElement("summary");
    sum.textContent = "¿Por qué?";
    const ul = document.createElement("ul");
    for (const s of visible.senales) {
      const item = document.createElement("li");
      item.textContent = s.descripcion;
      ul.append(item);
    }
    const nota = document.createElement("p");
    nota.className = "ayuda";
    nota.textContent = "El nivel tiene en cuenta también las frases anteriores de la conversación.";
    det.append(sum, ul, nota);
    li.append(det);
  }

  $("#conversacion").append(li);
  $("#conv-vacia").classList.add("oculto");
}

function mostrarError(texto) {
  $("#texto-error").textContent = texto || "";
}

function ocupado(si) {
  estado.ocupado = si;
  for (const b of document.querySelectorAll("button")) b.disabled = si;
  $("#analizar-texto").textContent = si ? "Analizando…" : "Analizar frase";
  $("#analizando").classList.toggle("oculto", !si);
}

async function procesar(texto, hablante) {
  const r = await enviarFrase(texto, hablante);
  agregarFrase(texto, hablante, r);
  mostrarNivel(r.decision_visible);
  if (r.mostrar_aviso) mostrarAlerta(r.decision_visible);
}

async function alEnviar(evento) {
  evento.preventDefault();
  if (estado.ocupado) return;
  const campo = $("#texto");
  const texto = campo.value.trim();
  mostrarError("");
  if (!texto) {
    mostrarError("Escribe una frase antes de analizar.");
    campo.focus();
    return;
  }
  const hablante = document.querySelector('input[name="hablante"]:checked').value;
  ocupado(true);
  try {
    await procesar(texto, hablante);
    campo.value = "";
  } catch (e) {
    mostrarError(e.message);
  } finally {
    ocupado(false);
    if ($("#alerta").classList.contains("oculto")) campo.focus();
  }
}

async function correrEjemplo(nombre) {
  if (estado.ocupado) return;
  mostrarError("");
  ocupado(true);
  const boton = document.querySelector(`[data-ejemplo="${nombre}"]`);
  boton.classList.add("reproduciendo");
  try {
    await nuevaConversacion();
    for (const [hablante, texto] of EJEMPLOS[nombre]) {
      await procesar(texto, hablante);
      await new Promise((ok) => setTimeout(ok, 500));
    }
  } catch (e) {
    mostrarError(e.message);
  } finally {
    boton.classList.remove("reproduciendo");
    ocupado(false);
  }
}

// ---- Audio: grabación con el micrófono o archivo, transcrito en el servidor local ----

const MAX_AUDIO = 10 * 1024 * 1024;
const grabacion = { recorder: null, partes: [], reloj: null, inicio: 0 };

function estadoAudio(texto, grabando = false) {
  const p = $("#audio-estado");
  p.textContent = texto;
  p.classList.toggle("grabando", grabando);
}

function hayConsentimiento() {
  if ($("#consentimiento").checked) return true;
  estadoAudio("Marca la casilla de consentimiento antes de grabar o subir un audio.");
  $("#consentimiento").focus();
  return false;
}

async function enviarAudio(blob, nombre) {
  if (blob.size > MAX_AUDIO) {
    estadoAudio("El audio supera los 10 MB. Prueba con uno más corto.");
    return;
  }
  ocupado(true);
  estadoAudio("Transcribiendo en este equipo… puede tardar un poco.");
  try {
    if (!estado.llamadaId) await nuevaConversacion();
    const datos = new FormData();
    datos.append("audio", blob, nombre);
    datos.append("consentimiento", "true");
    let r;
    try {
      r = await fetch(`/llamadas/${estado.llamadaId}/audio`, { method: "POST", body: datos });
    } catch {
      throw new Error("No pudimos conectar con Centinela. Revisa que el servidor esté encendido.");
    }
    if (!r.ok) {
      const cuerpo = await r.json().catch(() => ({}));
      const detalle = typeof cuerpo.detail === "string" ? cuerpo.detail : mensajeDeError(r.status);
      throw new Error(detalle);
    }
    const res = await r.json();
    if (!res.resultados.length) {
      estadoAudio("No encontramos voz en el audio.");
      return;
    }
    for (const item of res.resultados) {
      agregarFrase(item.fragmento.texto, "audio", item);
      mostrarNivel(item.decision_visible);
      if (item.mostrar_aviso) mostrarAlerta(item.decision_visible);
    }
    estado.ultimoFin = res.resultados.at(-1).fragmento.fin;
    estadoAudio(`Listo: se analizaron ${res.resultados.length} fragmentos del audio. El audio ya se descartó.`);
  } catch (e) {
    estadoAudio(e.message);
  } finally {
    ocupado(false);
  }
}

async function empezarGrabacion() {
  if (!hayConsentimiento()) return;
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
    estadoAudio("Este navegador no permite grabar. Sube un archivo de audio en su lugar.");
    return;
  }
  let flujo;
  try {
    flujo = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    estadoAudio("No se pudo usar el micrófono. Revisa el permiso del navegador o sube un archivo.");
    return;
  }
  grabacion.partes = [];
  grabacion.recorder = new MediaRecorder(flujo);
  grabacion.recorder.addEventListener("dataavailable", (e) => e.data.size && grabacion.partes.push(e.data));
  grabacion.recorder.addEventListener("stop", () => {
    flujo.getTracks().forEach((t) => t.stop());
    clearInterval(grabacion.reloj);
    $("#detener").classList.add("oculto");
    $("#grabar").classList.remove("oculto");
    const blob = new Blob(grabacion.partes, { type: grabacion.recorder.mimeType || "audio/webm" });
    grabacion.partes = [];
    enviarAudio(blob, "grabacion.webm");
  });
  grabacion.recorder.start();
  grabacion.inicio = Date.now();
  $("#grabar").classList.add("oculto");
  $("#detener").classList.remove("oculto");
  $("#detener").focus();
  const tic = () => {
    const s = Math.floor((Date.now() - grabacion.inicio) / 1000);
    estadoAudio(`Grabando ${Math.floor(s / 60)}:${String(s % 60).padStart(2, "0")}`, true);
  };
  tic();
  grabacion.reloj = setInterval(tic, 1000);
}

// ---- Asistente por voz ----

const asistente = { recorder: null, partes: [], audio: null };

function mostrarRespuesta(r, dijiste) {
  $("#respuesta").classList.remove("oculto");
  $("#dijiste").textContent = dijiste ? `Dijiste: «${dijiste}»` : "";
  $("#respuesta-texto").textContent = r.respuesta;
  $("#respuesta-nota").textContent = r.requiere_confirmacion
    ? "Por seguridad, la voz no puede cambiar tu cuenta ni tu protección."
    : "";
  if ($("#en-voz-alta").checked) leerEnVozAlta(r.respuesta);
}

async function leerEnVozAlta(texto) {
  // Primero la voz de Piper en este equipo; si no está instalada, la del navegador
  try {
    const r = await fetch("/voz", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ texto }) });
    if (r.ok) {
      const url = URL.createObjectURL(await r.blob());
      asistente.audio?.pause();
      asistente.audio = new Audio(url);
      asistente.audio.addEventListener("ended", () => URL.revokeObjectURL(url));
      await asistente.audio.play();
      return;
    }
  } catch { /* se intenta con la voz del navegador */ }
  if ("speechSynthesis" in window) {
    speechSynthesis.cancel();
    const u = new SpeechSynthesisUtterance(texto);
    u.lang = "es-CO";
    speechSynthesis.speak(u);
  }
}

async function preguntar(texto) {
  const cuerpo = { texto };
  if (estado.llamadaId) cuerpo.llamada_id = estado.llamadaId;
  try {
    const r = await api("/asistente", { method: "POST", body: JSON.stringify(cuerpo) });
    mostrarRespuesta(r, null);
  } catch (e) {
    mostrarRespuesta({ respuesta: e.message }, null);
  }
}

async function empezarAHablar() {
  if (!navigator.mediaDevices?.getUserMedia || typeof MediaRecorder === "undefined") {
    mostrarRespuesta({ respuesta: "Este navegador no permite usar el micrófono. Escribe tu pregunta." }, null);
    return;
  }
  let flujo;
  try {
    flujo = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch {
    mostrarRespuesta({ respuesta: "No se pudo usar el micrófono. Revisa el permiso del navegador o escribe tu pregunta." }, null);
    return;
  }
  asistente.partes = [];
  asistente.recorder = new MediaRecorder(flujo);
  asistente.recorder.addEventListener("dataavailable", (e) => e.data.size && asistente.partes.push(e.data));
  asistente.recorder.addEventListener("stop", async () => {
    flujo.getTracks().forEach((t) => t.stop());
    $("#dejar-hablar").classList.add("oculto");
    $("#hablar").classList.remove("oculto");
    $("#hablar").focus();
    const blob = new Blob(asistente.partes, { type: asistente.recorder.mimeType || "audio/webm" });
    asistente.partes = [];
    $("#respuesta").classList.remove("oculto");
    $("#dijiste").textContent = "";
    $("#respuesta-texto").textContent = "Escuchando lo que dijiste…";
    $("#respuesta-nota").textContent = "";
    const datos = new FormData();
    datos.append("audio", blob, "orden.webm");
    // Quien pulsa el botón consiente grabar su propia voz para esta orden
    datos.append("consentimiento", "true");
    if (estado.llamadaId) datos.append("llamada_id", estado.llamadaId);
    try {
      const r = await fetch("/asistente/voz", { method: "POST", body: datos });
      const cuerpo = await r.json().catch(() => ({}));
      if (!r.ok) throw new Error(typeof cuerpo.detail === "string" ? cuerpo.detail : mensajeDeError(r.status));
      mostrarRespuesta(cuerpo, cuerpo.transcripcion);
    } catch (e) {
      const texto = e instanceof TypeError ? "No pudimos conectar con Centinela." : e.message;
      mostrarRespuesta({ respuesta: `${texto} Mientras tanto, puedes escribir tu pregunta.` }, null);
    }
  });
  asistente.recorder.start();
  $("#hablar").classList.add("oculto");
  $("#dejar-hablar").classList.remove("oculto");
  $("#dejar-hablar").focus();
}

async function cargarSugerencias() {
  try {
    const comandos = await api("/asistente/comandos");
    const caja = $("#sugerencias");
    const orden = ["parece_estafa", "explicar_alerta", "verificar_identidad", "ayuda"];
    const elegidos = orden.map((id) => comandos.find((c) => c.id === id)).filter(Boolean);
    for (const c of elegidos) {
      const b = document.createElement("button");
      b.type = "button";
      b.textContent = c.ejemplo;
      b.addEventListener("click", () => preguntar(c.ejemplo));
      caja.append(b);
    }
  } catch { /* las sugerencias son opcionales */ }
}

// ---- Número que llama: consulta y reporte ----

function pintarReputacion(r) {
  const caja = $("#numero-resultado");
  caja.textContent = r.mensaje;
  caja.dataset.estado = r.estado;
  caja.classList.remove("oculto");
}

async function consultarNumero() {
  const numero = $("#numero").value.trim();
  const boton = $("#consultar-numero");
  if (!numero) { $("#numero-aviso").textContent = "Escribe el número que te llama."; $("#numero").focus(); return; }
  boton.disabled = true;
  try {
    const r = await fetch("/numeros/consulta", {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ numero }),
    });
    const datos = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(typeof datos.detail === "string" ? datos.detail : "Escribe un número válido, por ejemplo 300 123 4567.");
    $("#numero-aviso").textContent = "";
    pintarReputacion(datos);
  } catch (e) {
    $("#numero-aviso").textContent = e instanceof TypeError ? "No pudimos conectar con Centinela." : e.message;
  } finally {
    boton.disabled = false;
  }
}

async function enviarReporte(ev) {
  ev.preventDefault();
  const numero = $("#numero").value.trim();
  const estadoReporte = $("#reporte-estado");
  if (!numero) { estadoReporte.textContent = "Primero escribe el número que quieres reportar."; $("#numero").focus(); return; }
  const boton = ev.submitter || ev.target.querySelector("button");
  boton.disabled = true;
  estadoReporte.replaceChildren();
  try {
    const r = await fetch("/reportes", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Centinela": "1" },
      body: JSON.stringify(cuerpoReporte(numero)),
    });
    const datos = await r.json().catch(() => ({}));
    if (r.status === 401) {
      const enlace = document.createElement("a");
      enlace.href = "/cuenta.html";
      enlace.textContent = "Entra a tu cuenta";
      estadoReporte.append(enlace, " para reportar. Así evitamos reportes falsos en masa.");
      return;
    }
    if (!r.ok) throw new Error(typeof datos.detail === "string" ? datos.detail : "Revisa el número y el motivo.");
    estadoReporte.textContent = "Gracias. Tu reporte quedó guardado; nadie más verá que fuiste tú."
      + (datos.respaldado ? " Como analizaste esta llamada aquí, tu reporte vale más." : "")
      + (datos.cuenta_nueva ? " Empezará a contar cuando tu cuenta cumpla un día." : "");
    pintarReputacion(datos);
  } catch (e) {
    estadoReporte.textContent = e instanceof TypeError ? "No pudimos conectar con Centinela." : e.message;
  } finally {
    boton.disabled = false;
  }
}

const RESULTADOS_ESTAFA = ["perdida", "intento"];

function resultadoElegido() {
  const r = document.querySelector('input[name="resultado"]:checked');
  return r ? r.value : "intento";
}

function cuerpoReporte(numero) {
  const resultado = resultadoElegido();
  const cuerpo = { numero, resultado };
  if (RESULTADOS_ESTAFA.includes(resultado)) cuerpo.categoria = $("#categoria").value;
  // La conversación analizada respalda el reporte si es sobre este mismo número
  if (estado.llamadaId && estado.numeroAplicado === numero) cuerpo.llamada_id = estado.llamadaId;
  return cuerpo;
}

async function cargarResultados() {
  try {
    const resultados = await api("/reportes/resultados");
    for (const r of resultados) {
      const label = document.createElement("label");
      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "resultado";
      radio.value = r.id;
      radio.checked = r.id === "intento";
      radio.addEventListener("change", () => {
        $("#caja-categoria").classList.toggle("oculto", !RESULTADOS_ESTAFA.includes(r.id));
      });
      const texto = document.createElement("span");
      texto.textContent = r.descripcion;
      label.append(radio, texto);
      $("#resultados").append(label);
    }
  } catch { /* sin opciones se reporta como intento */ }
}

async function cargarCategorias() {
  cargarResultados();
  try {
    const categorias = await api("/reportes/categorias");
    for (const c of categorias) {
      const op = document.createElement("option");
      op.value = c.id;
      op.textContent = c.descripcion;
      $("#categoria").append(op);
    }
  } catch { /* sin categorías no se puede reportar; la consulta sigue funcionando */ }
}

// ---- Denuncia: resumen para presentar en el canal oficial; Centinela no lo envía ----

const FECHA_DENUNCIA = new Intl.DateTimeFormat("es-CO", { dateStyle: "long", timeStyle: "short" });

function resumenDenuncia() {
  const frases = [...document.querySelectorAll("#conversacion > li")];
  const numero = $("#numero").value.trim();
  const perdida = $("#denuncia-perdida").checked;
  const senales = new Set();
  const lineas = [
    "RESUMEN PARA DENUNCIA (preparado con Centinela, versión de prueba)",
    "",
    `Fecha y hora del resumen: ${FECHA_DENUNCIA.format(new Date())}`,
    `Número que llamó: ${numero || "(no lo escribí)"} — el número en pantalla puede estar suplantado.`,
    `¿Hubo pérdida de dinero o datos?: ${perdida ? "Sí" : "No"}`,
    "",
    "Lo que se dijo en la llamada:",
  ];
  if (!frases.length) lineas.push("(No analicé la conversación en Centinela. Describe aquí lo que te dijeron.)");
  for (const li of frases) {
    const quien = li.querySelector(".frase-quien")?.textContent || "Quien llama";
    const texto = li.querySelector(".frase-texto")?.textContent || "";
    const nivel = li.querySelector(".frase-nivel")?.textContent || "";
    lineas.push(`- ${quien}: "${texto}"${nivel ? ` [${nivel}]` : ""}`);
    for (const s of li.querySelectorAll("details li")) senales.add(s.textContent);
  }
  if (senales.size) {
    lineas.push("", "Señales de estafa que detectó Centinela:");
    for (const s of senales) lineas.push(`- ${s}`);
  }
  lineas.push(
    "",
    "Datos que debo agregar: mi nombre y documento, a dónde envié dinero (banco, cuenta, Nequi, Daviplata), montos, horas exactas y capturas de pantalla.",
    "Centinela es una herramienta de apoyo y puede equivocarse; este resumen no es una prueba por sí solo.",
  );
  // La línea 165 es para extorsión o amenazas contra la persona, no para "su cuenta será bloqueada"
  const dicho = frases.map((li) => li.querySelector(".frase-texto")?.textContent || "").join(" ");
  const extorsion = /extors|vacuna|secuestr|le caemos|ubicad|le va a pasar|le va a ir mal|quem(ar|amos)|su familia|tenemos a/i.test(dicho);
  return { texto: lineas.join("\n"), extorsion };
}

function prepararDenuncia() {
  const { texto, extorsion } = resumenDenuncia();
  $("#denuncia-texto").value = texto;
  $("#canal-165").classList.toggle("oculto", !extorsion);
  $("#canal-banco").classList.toggle("oculto", !$("#denuncia-perdida").checked);
  $("#denuncia-lista").classList.remove("oculto");
  $("#denuncia-estado").textContent = "";
  $("#denuncia-texto").focus();
  $("#denuncia-texto").scrollTop = 0;
}

async function copiarDenuncia() {
  try {
    await navigator.clipboard.writeText($("#denuncia-texto").value);
    $("#denuncia-estado").textContent = "Copiado. Pégalo en el formulario de denuncia.";
  } catch {
    $("#denuncia-texto").select();
    $("#denuncia-estado").textContent = "Selecciona el texto y cópialo con el menú del celular.";
  }
}

function descargarDenuncia() {
  const archivo = new Blob([$("#denuncia-texto").value], { type: "text/plain;charset=utf-8" });
  const enlace = document.createElement("a");
  enlace.href = URL.createObjectURL(archivo);
  enlace.download = `denuncia-centinela-${new Date().toISOString().slice(0, 10)}.txt`;
  enlace.click();
  setTimeout(() => URL.revokeObjectURL(enlace.href), 1000);
  $("#denuncia-estado").textContent = "Descargado en tu celular. Adjúntalo en la denuncia.";
}

function pintarMensaje(r) {
  const caja = $("#msj-resultado");
  caja.dataset.nivel = r.nivel;
  $("#msj-nivel").textContent = `Riesgo ${ETIQUETAS[r.nivel].toLowerCase()}`;
  $("#msj-texto").textContent = r.mensaje;
  const lista = $("#msj-enlaces");
  lista.replaceChildren();
  for (const e of r.enlaces) {
    const li = document.createElement("li");
    li.dataset.oficial = e.oficial ? "si" : "no";
    const nombre = document.createElement("strong");
    nombre.textContent = e.dominio;
    li.append(nombre);
    if (e.hallazgos.length) {
      const ul = document.createElement("ul");
      for (const h of e.hallazgos) {
        const item = document.createElement("li");
        item.textContent = `El enlace ${h}.`;
        ul.append(item);
      }
      li.append(ul);
    } else if (!e.oficial) {
      li.append(" Sin hallazgos en cómo está escrito.");
    }
    lista.append(li);
  }
  $("#msj-limite").textContent = r.limite;
  caja.classList.remove("oculto");
}

async function revisarMensaje(ev) {
  ev.preventDefault();
  const texto = $("#texto-mensaje").value.trim();
  const boton = $("#revisar-mensaje");
  if (!texto) { $("#mensaje-error").textContent = "Pega el mensaje que recibiste."; $("#texto-mensaje").focus(); return; }
  boton.disabled = true;
  try {
    const r = await api("/mensajes/analizar", { method: "POST", body: JSON.stringify({ texto }) });
    $("#mensaje-error").textContent = "";
    pintarMensaje(r);
  } catch (e) {
    $("#mensaje-error").textContent = e.status === 422 ? "El mensaje es demasiado largo (máximo 2000 caracteres)." : e.message;
  } finally {
    boton.disabled = false;
  }
}

async function cargarCatalogo() {
  try {
    const senales = await api("/senales");
    const lista = $("#catalogo");
    for (const s of senales) {
      const li = document.createElement("li");
      li.textContent = s.descripcion;
      lista.append(li);
    }
  } catch {
    $("#catalogo").textContent = "No se pudo cargar la lista de señales.";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  mostrarNivel(null);
  $("#formulario").addEventListener("submit", alEnviar);
  $("#texto").addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      $("#formulario").requestSubmit();
    }
  });
  $("#nueva").addEventListener("click", async () => {
    mostrarError("");
    try { await nuevaConversacion(); } catch (e) { mostrarError(e.message); }
    $("#texto").focus();
  });
  $("#cerrar-alerta").addEventListener("click", () => {
    $("#alerta").classList.add("oculto");
    $("#texto").focus();
  });
  for (const b of document.querySelectorAll("[data-ejemplo]")) {
    b.addEventListener("click", () => correrEjemplo(b.dataset.ejemplo));
  }
  $("#consultar-numero").addEventListener("click", consultarNumero);
  $("#form-reporte").addEventListener("submit", enviarReporte);
  $("#numero").addEventListener("change", () => {
    $("#numero-resultado").classList.add("oculto");
    if (!estado.llamadaId || $("#numero").value.trim() === estado.numeroAplicado) return;
    if ($("#conversacion").childElementCount === 0) {
      estado.llamadaId = null; // la próxima frase empieza la conversación con este número
    } else {
      $("#numero-aviso").textContent = "Para que Centinela tenga en cuenta este número, empieza una nueva conversación.";
    }
  });
  cargarCategorias();
  $("#grabar").addEventListener("click", empezarGrabacion);
  $("#detener").addEventListener("click", () => grabacion.recorder?.stop());
  $("#archivo").addEventListener("change", (e) => {
    const archivo = e.target.files[0];
    e.target.value = "";
    if (archivo && !estado.ocupado && hayConsentimiento()) enviarAudio(archivo, archivo.name);
  });
  $("#hablar").addEventListener("click", empezarAHablar);
  $("#dejar-hablar").addEventListener("click", () => asistente.recorder?.stop());
  $("#form-pregunta").addEventListener("submit", (e) => {
    e.preventDefault();
    const texto = $("#pregunta").value.trim();
    if (!texto) {
      $("#pregunta").focus();
      return;
    }
    $("#pregunta").value = "";
    preguntar(texto);
  });
  cargarSugerencias();
  cargarCatalogo();
  $("#form-mensaje").addEventListener("submit", revisarMensaje);
  $("#preparar-denuncia").addEventListener("click", prepararDenuncia);
  $("#copiar-denuncia").addEventListener("click", copiarDenuncia);
  $("#descargar-denuncia").addEventListener("click", descargarDenuncia);
});
