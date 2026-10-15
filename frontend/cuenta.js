"use strict";

// Pantalla de cuenta. Todo texto se inserta con textContent (modelo de amenazas, A5).
// Cada solicitud que cambia algo lleva la cabecera X-Centinela (A3).

const $ = (sel) => document.querySelector(sel);

const FECHA = new Intl.DateTimeFormat("es-CO", { dateStyle: "medium", timeStyle: "short" });
const DIA = new Intl.DateTimeFormat("es-CO", { dateStyle: "long" });
const NIVELES = { bajo: "Bajo", moderado: "Moderado", alto: "Alto", critico: "Crítico" };
const HABLANTES = { llamante: "La persona que llama", usuario: "Yo" };
let guardaHistorial = false;

async function api(ruta, { metodo = "GET", datos } = {}) {
  const opciones = { method: metodo, headers: {}, credentials: "same-origin" };
  if (metodo !== "GET") opciones.headers["X-Centinela"] = "1";
  if (datos !== undefined) {
    opciones.headers["Content-Type"] = "application/json";
    opciones.body = JSON.stringify(datos);
  }
  let r;
  try {
    r = await fetch(ruta, opciones);
  } catch {
    throw new Error("No pudimos conectar con Centinela. Revisa que el servidor esté encendido.");
  }
  const cuerpo = await r.json().catch(() => ({}));
  if (!r.ok) {
    const error = new Error(textoDeError(r.status, cuerpo.detail));
    error.status = r.status;
    throw error;
  }
  return cuerpo;
}

function textoDeError(status, detalle) {
  // Los errores de validación de Pydantic llegan como lista; se traduce a algo comprensible
  if (Array.isArray(detalle)) {
    const msg = detalle.map((d) => String(d.msg || "")).find((m) => m.includes("PIN") || m.includes("alias"));
    if (msg) return msg.replace(/^Value error, /, "");
    return "Revisa los datos: el alias debe tener de 3 a 30 caracteres y el PIN de 6 a 12 números.";
  }
  if (typeof detalle === "string") return detalle;
  return status === 429 ? "Demasiados intentos. Espera un momento." : "Algo salió mal. Intenta de nuevo.";
}

function avisar(texto, tipo = "ok") {
  const m = $("#mensaje");
  m.textContent = texto;
  m.dataset.tipo = tipo;
  m.classList.remove("oculto");
  m.focus();
}

function ocupado(boton, si) {
  boton.disabled = si;
  boton.setAttribute("aria-busy", String(si));
}

// ---- Conversión WebAuthn (base64url <-> ArrayBuffer) para navegadores sin los métodos JSON ----

function aBuffer(b64url) {
  const b64 = b64url.replace(/-/g, "+").replace(/_/g, "/").padEnd(Math.ceil(b64url.length / 4) * 4, "=");
  return Uint8Array.from(atob(b64), (c) => c.charCodeAt(0)).buffer;
}

function aB64url(buffer) {
  let s = "";
  for (const b of new Uint8Array(buffer)) s += String.fromCharCode(b);
  return btoa(s).replace(/\+/g, "-").replace(/\//g, "_").replace(/=+$/, "");
}

function opcionesDeCreacion(o) {
  if (PublicKeyCredential.parseCreationOptionsFromJSON) return PublicKeyCredential.parseCreationOptionsFromJSON(o);
  return {
    ...o,
    challenge: aBuffer(o.challenge),
    user: { ...o.user, id: aBuffer(o.user.id) },
    excludeCredentials: (o.excludeCredentials || []).map((c) => ({ ...c, id: aBuffer(c.id) })),
  };
}

function opcionesDeEntrada(o) {
  if (PublicKeyCredential.parseRequestOptionsFromJSON) return PublicKeyCredential.parseRequestOptionsFromJSON(o);
  return {
    ...o,
    challenge: aBuffer(o.challenge),
    allowCredentials: (o.allowCredentials || []).map((c) => ({ ...c, id: aBuffer(c.id) })),
  };
}

function credencialAJson(c) {
  if (typeof c.toJSON === "function") {
    try { return c.toJSON(); } catch { /* algunos navegadores fallan con ciertas extensiones */ }
  }
  const r = c.response;
  const respuesta = { clientDataJSON: aB64url(r.clientDataJSON) };
  if (r.attestationObject) {
    respuesta.attestationObject = aB64url(r.attestationObject);
    if (r.getTransports) respuesta.transports = r.getTransports();
  } else {
    respuesta.authenticatorData = aB64url(r.authenticatorData);
    respuesta.signature = aB64url(r.signature);
    if (r.userHandle) respuesta.userHandle = aB64url(r.userHandle);
  }
  return {
    id: c.id, rawId: aB64url(c.rawId), type: c.type, response: respuesta,
    clientExtensionResults: c.getClientExtensionResults ? c.getClientExtensionResults() : {},
    authenticatorAttachment: c.authenticatorAttachment || undefined,
  };
}

const hayPasskeys = () => typeof window.PublicKeyCredential === "function" && !!navigator.credentials;

function errorDePasskey(e) {
  if (e && e.name === "NotAllowedError") return "Se canceló la passkey o se agotó el tiempo. Intenta de nuevo.";
  if (e && e.name === "InvalidStateError") return "Este dispositivo ya tiene una passkey para tu cuenta.";
  if (e && e.name === "SecurityError") return "Las passkeys solo funcionan si abres Centinela en http://localhost:8000 o por HTTPS.";
  return e && e.message ? e.message : "No se pudo usar la passkey.";
}

// ---- Vistas ----

async function cargar() {
  $("#cargando").classList.remove("oculto");
  try {
    const cuenta = await api("/cuenta");
    await mostrarCuenta(cuenta);
  } catch (e) {
    if (e.status !== 401) avisar(e.message, "error");
    mostrarEntrar();
  } finally {
    $("#cargando").classList.add("oculto");
  }
}

function mostrarEntrar() {
  $("#vista-cuenta").classList.add("oculto");
  $("#vista-entrar").classList.remove("oculto");
  if (!hayPasskeys()) $("#entrar-passkey").classList.add("oculto");
}

async function mostrarCuenta(cuenta) {
  $("#vista-entrar").classList.add("oculto");
  $("#vista-cuenta").classList.remove("oculto");
  $("#alias").textContent = cuenta.alias;
  $("#avatar").textContent = cuenta.alias.charAt(0).toUpperCase();
  pintarPasskeys(cuenta.passkeys);
  pintarPermisos(cuenta.consentimientos);
  guardaHistorial = cuenta.consentimientos.some((c) => c.finalidad === "guardar_historial" && c.otorgado);
  await cargarHistorial();
  await cargarReportes();
  if (!hayPasskeys()) {
    $("#form-passkey").classList.add("oculto");
    $("#passkey-no-soportada").classList.remove("oculto");
  }
  await cargarSesiones();
}

function pintarPasskeys(passkeys) {
  const lista = $("#passkeys");
  lista.replaceChildren();
  $("#passkeys-vacia").classList.toggle("oculto", passkeys.length > 0);
  $("#total-passkeys").textContent = passkeys.length;
  for (const p of passkeys) {
    const li = document.createElement("li");
    const info = document.createElement("div");
    const nombre = document.createElement("strong");
    nombre.textContent = p.nombre;
    const fecha = document.createElement("p");
    fecha.className = "ayuda";
    fecha.textContent = `Agregada el ${FECHA.format(p.creada * 1000)}`;
    info.append(nombre, fecha);

    // Quitar una passkey pide el PIN en pantalla (A18), sin ventanas emergentes
    const detalles = document.createElement("details");
    const resumen = document.createElement("summary");
    resumen.textContent = "Quitar";
    const form = document.createElement("form");
    form.className = "fila";
    const etiqueta = document.createElement("label");
    etiqueta.className = "visualmente-oculto";
    const campo = document.createElement("input");
    campo.type = "password";
    campo.inputMode = "numeric";
    campo.maxLength = 12;
    campo.placeholder = "Tu PIN";
    campo.id = `pin-${p.id.slice(0, 12)}`;
    etiqueta.htmlFor = campo.id;
    etiqueta.textContent = `PIN para quitar ${p.nombre}`;
    const boton = document.createElement("button");
    boton.type = "submit";
    boton.className = "boton-peligro";
    boton.textContent = "Confirmar";
    form.append(etiqueta, campo, boton);
    form.addEventListener("submit", async (ev) => {
      ev.preventDefault();
      ocupado(boton, true);
      try {
        await api(`/cuenta/passkeys/${encodeURIComponent(p.id)}/eliminar`, { metodo: "POST", datos: { pin: campo.value } });
        avisar(`Quitamos la passkey "${p.nombre}".`);
        await recargarCuenta();
      } catch (e) {
        avisar(e.message, "error");
      } finally {
        ocupado(boton, false);
      }
    });
    detalles.append(resumen, form);
    li.append(info, detalles);
    lista.append(li);
  }
}

function pintarPermisos(consentimientos) {
  const lista = $("#permisos");
  lista.replaceChildren();
  for (const c of consentimientos) {
    const li = document.createElement("li");
    const label = document.createElement("label");
    label.className = "consentimiento";
    const caja = document.createElement("input");
    caja.type = "checkbox";
    caja.checked = c.otorgado;
    caja.disabled = !c.disponible;
    const texto = document.createElement("span");
    texto.textContent = c.descripcion;
    label.append(caja, texto);
    li.append(label);
    caja.addEventListener("change", async () => {
      caja.disabled = true;
      try {
        await api("/cuenta/consentimientos", { metodo: "PUT", datos: { finalidad: c.finalidad, otorgado: caja.checked } });
        if (c.finalidad === "guardar_historial") {
          guardaHistorial = caja.checked;
          await cargarHistorial();
          avisar(caja.checked
            ? "Desde ahora guardamos tus conversaciones nuevas."
            : "Permiso retirado. Borramos tu historial guardado.");
        } else {
          avisar(caja.checked ? "Permiso concedido." : "Permiso retirado.");
        }
      } catch (e) {
        caja.checked = !caja.checked;
        avisar(e.message, "error");
      } finally {
        caja.disabled = false;
      }
    });
    lista.append(li);
  }
}

// ---- Historial ----

function insignia(nivel, prefijo) {
  const s = document.createElement("span");
  s.className = "frase-nivel";
  s.dataset.nivel = nivel;
  const icono = document.createElement("span");
  icono.className = "nivel-icono";
  icono.setAttribute("aria-hidden", "true");
  const texto = document.createElement("span");
  texto.textContent = prefijo === "Riesgo" ? `Riesgo ${(NIVELES[nivel] || nivel).toLowerCase()}` : `${prefijo}: ${NIVELES[nivel] || nivel}`;
  s.append(icono, texto);
  return s;
}

async function cargarHistorial() {
  const { dias_retencion, llamadas } = await api("/historial");
  $("#historial-estado").textContent = guardaHistorial
    ? `Guardamos tus conversaciones durante ${dias_retencion} días y luego se borran solas.`
    : "No estamos guardando tus conversaciones. Si quieres conservarlas, activa \"Guardar el historial\" en Permisos.";
  const lista = $("#historial");
  lista.replaceChildren();
  for (const l of llamadas) lista.append(itemDeHistorial(l));
  if (!llamadas.length && guardaHistorial) {
    const li = document.createElement("li");
    li.className = "ayuda";
    li.textContent = "Todavía no hay conversaciones guardadas. Analiza una en la página principal.";
    lista.append(li);
  }
  $("#borrar-historial").classList.toggle("oculto", llamadas.length === 0);
  $("#total-conversaciones").textContent = llamadas.length;
  $("#confirmar-borrado").classList.add("oculto");
}

function itemDeHistorial(l) {
  const li = document.createElement("li");
  const info = document.createElement("div");
  const fecha = document.createElement("strong");
  fecha.textContent = FECHA.format(new Date(l.creada));
  const datos = document.createElement("p");
  datos.className = "ayuda";
  datos.textContent = `${l.frases === 1 ? "1 frase" : `${l.frases} frases`}${l.aviso_visible ? " · se mostró una alerta" : ""}`
    + ` · se borra el ${DIA.format(new Date(l.borrar_el))}`;
  info.append(fecha, document.createElement("br"), insignia(l.nivel_max, "Nivel más alto"), datos);

  const detalles = document.createElement("details");
  const resumen = document.createElement("summary");
  resumen.textContent = "Ver conversación";
  const frases = document.createElement("ol");
  frases.className = "conversacion";
  detalles.append(resumen, frases);
  detalles.addEventListener("toggle", async () => {
    if (!detalles.open || frases.childElementCount) return;
    try {
      const d = await api(`/historial/${encodeURIComponent(l.id)}`);
      for (const f of d.fragmentos) {
        const visible = f.decisiones.find((x) => x.estrategia === d.estrategia_visible) || f.decisiones[0];
        const item = document.createElement("li");
        item.className = "frase";
        item.dataset.nivel = visible.nivel;
        item.dataset.hablante = f.hablante;
        const quien = document.createElement("p");
        quien.className = "frase-quien";
        quien.textContent = HABLANTES[f.hablante] || "Del audio";
        const texto = document.createElement("p");
        texto.className = "frase-texto";
        texto.textContent = f.texto;
        item.append(quien, texto, insignia(visible.nivel, "Riesgo"));
        frases.append(item);
      }
    } catch (e) {
      avisar(e.message, "error");
    }
  });

  const borrar = document.createElement("button");
  borrar.type = "button";
  borrar.className = "boton-secundario";
  borrar.textContent = "Borrar";
  borrar.setAttribute("aria-label", `Borrar la conversación del ${FECHA.format(new Date(l.creada))}`);
  borrar.addEventListener("click", async () => {
    ocupado(borrar, true);
    try {
      await api(`/historial/${encodeURIComponent(l.id)}`, { metodo: "DELETE" });
      avisar("Borramos esa conversación.");
      await cargarHistorial();
    } catch (e) {
      avisar(e.message, "error");
      ocupado(borrar, false);
    }
  });
  li.append(info, borrar, detalles);
  return li;
}

// ---- Reportes ----

async function cargarReportes() {
  const reportes = await api("/reportes/mios");
  const lista = $("#reportes");
  lista.replaceChildren();
  $("#reportes-vacia").classList.toggle("oculto", reportes.length > 0);
  $("#total-reportes").textContent = reportes.length;
  for (const r of reportes) {
    const li = document.createElement("li");
    const info = document.createElement("div");
    const numero = document.createElement("strong");
    numero.textContent = `Número terminado en ${r.terminacion}`;
    const datos = document.createElement("p");
    datos.className = "ayuda";
    datos.textContent = `${r.descripcion}${r.respaldado ? " · respaldado por un análisis" : ""} · ${FECHA.format(r.creado * 1000)}`;
    info.append(numero, datos);
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "boton-secundario";
    boton.textContent = "Retirar";
    boton.setAttribute("aria-label", `Retirar el reporte del número terminado en ${r.terminacion}`);
    boton.addEventListener("click", async () => {
      ocupado(boton, true);
      try {
        await api(`/reportes/${encodeURIComponent(r.id)}`, { metodo: "DELETE" });
        avisar("Retiramos tu reporte.");
        await cargarReportes();
      } catch (e) {
        avisar(e.message, "error");
        ocupado(boton, false);
      }
    });
    li.append(info, boton);
    lista.append(li);
  }
}

function nombreDeDispositivo(ua) {
  const so = /Android/.test(ua) ? "Android" : /iPhone|iPad/.test(ua) ? "iPhone o iPad" : /Windows/.test(ua) ? "Windows"
    : /Mac OS/.test(ua) ? "Mac" : /Linux/.test(ua) ? "Linux" : "";
  const nav = /Edg\//.test(ua) ? "Edge" : /Firefox\//.test(ua) ? "Firefox" : /Chrome\//.test(ua) ? "Chrome"
    : /Safari\//.test(ua) ? "Safari" : "";
  return so || nav ? [nav, so].filter(Boolean).join(" en ") : ua;
}

async function cargarSesiones() {
  const sesiones = await api("/cuenta/sesiones");
  const lista = $("#sesiones");
  lista.replaceChildren();
  for (const s of sesiones) {
    const li = document.createElement("li");
    const info = document.createElement("div");
    const nombre = document.createElement("strong");
    nombre.textContent = nombreDeDispositivo(s.dispositivo) + (s.actual ? " (este dispositivo)" : "");
    const uso = document.createElement("p");
    uso.className = "ayuda";
    uso.textContent = `Último uso: ${FECHA.format(s.ultimo_uso * 1000)}`;
    info.append(nombre, uso);
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "boton-secundario";
    boton.textContent = s.actual ? "Salir aquí" : "Cerrar sesión";
    boton.addEventListener("click", async () => {
      ocupado(boton, true);
      try {
        await api(`/cuenta/sesiones/${encodeURIComponent(s.id)}`, { metodo: "DELETE" });
        if (s.actual) { mostrarEntrar(); avisar("Cerraste la sesión en este dispositivo."); return; }
        avisar("Sesión cerrada en ese dispositivo.");
        await cargarSesiones();
      } catch (e) {
        avisar(e.message, "error");
        ocupado(boton, false);
      }
    });
    li.append(info, boton);
    lista.append(li);
  }
  $("#cerrar-otras").classList.toggle("oculto", sesiones.length < 2);
}

async function recargarCuenta() {
  await mostrarCuenta(await api("/cuenta"));
}

// ---- Acciones ----

$("#form-crear").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const error = $("#crear-error");
  const alias = $("#crear-alias").value.trim();
  const pin = $("#crear-pin").value;
  error.textContent = "";
  if (alias.length < 3) { error.textContent = "El alias debe tener al menos 3 caracteres."; $("#crear-alias").focus(); return; }
  if (!/^\d{6,12}$/.test(pin)) { error.textContent = "El PIN debe tener de 6 a 12 números."; $("#crear-pin").focus(); return; }
  if (pin !== $("#crear-pin2").value) { error.textContent = "Los PIN no coinciden."; $("#crear-pin2").focus(); return; }
  const boton = ev.submitter || ev.target.querySelector("button");
  ocupado(boton, true);
  try {
    await api("/cuenta/registro", { metodo: "POST", datos: { alias, pin } });
    ev.target.reset();
    await recargarCuenta();
    avisar("Cuenta creada. Si quieres, agrega una passkey para entrar sin el PIN.");
  } catch (e) {
    error.textContent = e.message;
  } finally {
    ocupado(boton, false);
  }
});

$("#form-entrar").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const error = $("#entrar-error");
  error.textContent = "";
  const boton = ev.submitter || ev.target.querySelector("button");
  ocupado(boton, true);
  try {
    await api("/cuenta/entrar", { metodo: "POST", datos: { alias: $("#entrar-alias").value, pin: $("#entrar-pin").value } });
    ev.target.reset();
    $("#mensaje").classList.add("oculto");
    await recargarCuenta();
  } catch (e) {
    error.textContent = e.message;
    $("#entrar-pin").value = "";
  } finally {
    ocupado(boton, false);
  }
});

$("#entrar-passkey").addEventListener("click", async (ev) => {
  const boton = ev.currentTarget;
  ocupado(boton, true);
  try {
    const { reto_id, opciones } = await api("/cuenta/passkey/opciones-entrada", { metodo: "POST" });
    const credencial = await navigator.credentials.get({ publicKey: opcionesDeEntrada(opciones) });
    await api("/cuenta/passkey/entrar", { metodo: "POST", datos: { reto_id, credencial: credencialAJson(credencial) } });
    $("#mensaje").classList.add("oculto");
    await recargarCuenta();
  } catch (e) {
    avisar(errorDePasskey(e), "error");
  } finally {
    ocupado(boton, false);
  }
});

$("#form-passkey").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const boton = ev.submitter || ev.target.querySelector("button");
  ocupado(boton, true);
  try {
    const { reto_id, opciones } = await api("/cuenta/passkeys/opciones", { metodo: "POST" });
    const credencial = await navigator.credentials.create({ publicKey: opcionesDeCreacion(opciones) });
    const nombre = $("#passkey-nombre").value.trim() || "Mi passkey";
    await api("/cuenta/passkeys", { metodo: "POST", datos: { reto_id, nombre, credencial: credencialAJson(credencial) } });
    await recargarCuenta();
    avisar("Passkey agregada. La próxima vez puedes entrar sin escribir el PIN.");
  } catch (e) {
    avisar(errorDePasskey(e), "error");
  } finally {
    ocupado(boton, false);
  }
});

$("#salir").addEventListener("click", async () => {
  try {
    await api("/cuenta/salir", { metodo: "POST" });
  } catch { /* si la sesión ya no existía, igual se muestra la entrada */ }
  mostrarEntrar();
  avisar("Saliste de tu cuenta.");
});

$("#cerrar-otras").addEventListener("click", async (ev) => {
  const boton = ev.currentTarget;
  ocupado(boton, true);
  try {
    const { cerradas } = await api("/cuenta/sesiones/cerrar-otras", { metodo: "POST" });
    avisar(cerradas === 1 ? "Cerramos 1 sesión." : `Cerramos ${cerradas} sesiones.`);
    await cargarSesiones();
  } catch (e) {
    avisar(e.message, "error");
  } finally {
    ocupado(boton, false);
  }
});

$("#form-eliminar").addEventListener("submit", async (ev) => {
  ev.preventDefault();
  const error = $("#eliminar-error");
  error.textContent = "";
  const boton = ev.submitter || ev.target.querySelector("button");
  ocupado(boton, true);
  try {
    await api("/cuenta/eliminar", { metodo: "POST", datos: { pin: $("#eliminar-pin").value } });
    ev.target.reset();
    mostrarEntrar();
    avisar("Eliminamos tu cuenta y todos sus datos.");
  } catch (e) {
    error.textContent = e.message;
  } finally {
    ocupado(boton, false);
  }
});

$("#borrar-historial").addEventListener("click", () => {
  $("#confirmar-borrado").classList.remove("oculto");
  $("#no-borrar").focus();
});
$("#no-borrar").addEventListener("click", () => {
  $("#confirmar-borrado").classList.add("oculto");
  $("#borrar-historial").focus();
});
$("#si-borrar").addEventListener("click", async (ev) => {
  const boton = ev.currentTarget;
  ocupado(boton, true);
  try {
    const { borradas } = await api("/historial", { metodo: "DELETE" });
    await cargarHistorial();
    avisar(borradas === 1 ? "Borramos 1 conversación." : `Borramos ${borradas} conversaciones.`);
  } catch (e) {
    avisar(e.message, "error");
  } finally {
    ocupado(boton, false);
  }
});

$("#exportar").addEventListener("click", async (ev) => {
  const boton = ev.currentTarget;
  ocupado(boton, true);
  try {
    const r = await fetch("/cuenta/exportar", { credentials: "same-origin" });
    if (!r.ok) throw new Error(r.status === 401 ? "Tu sesión terminó. Vuelve a entrar." : "No pudimos preparar el archivo.");
    const url = URL.createObjectURL(await r.blob());
    const enlace = document.createElement("a");
    enlace.href = url;
    enlace.download = "centinela-mis-datos.json";
    document.body.append(enlace);
    enlace.click();
    enlace.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    avisar("Descargamos tus datos en el archivo centinela-mis-datos.json.");
  } catch (e) {
    avisar(e.message, "error");
  } finally {
    ocupado(boton, false);
  }
});

cargar();
