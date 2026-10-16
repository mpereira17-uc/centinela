"use strict";

// Detalles de interfaz comunes a todas las pantallas: tamaño de letra, bienvenida,
// hoja de alerta (Escape y deslizar), vibración en alertas altas y animaciones.
// Todo el texto se inserta con textContent, nunca como HTML.

(() => {
  const $ = (sel) => document.querySelector(sel);
  const sinMovimiento = matchMedia("(prefers-reduced-motion: reduce)");

  // localStorage puede no estar disponible (modo privado, datos bloqueados)
  const guardado = {
    leer(clave) { try { return localStorage.getItem(clave); } catch { return null; } },
    escribir(clave, valor) { try { localStorage.setItem(clave, valor); } catch { /* sin almacenamiento */ } },
  };

  // ---- Tamaño de letra ----
  function aplicarLetra(grande) {
    document.documentElement.classList.toggle("letra-grande", grande);
    const b = $("#tamano-letra");
    if (b) {
      b.setAttribute("aria-pressed", String(grande));
      b.setAttribute("aria-label", grande ? "Usar letra normal" : "Usar letra grande");
    }
  }
  aplicarLetra(guardado.leer("centinela-letra") === "grande");

  function iniciarLetra() {
    const b = $("#tamano-letra");
    if (!b) return;
    aplicarLetra(document.documentElement.classList.contains("letra-grande"));
    b.addEventListener("click", () => {
      const grande = !document.documentElement.classList.contains("letra-grande");
      aplicarLetra(grande);
      guardado.escribir("centinela-letra", grande ? "grande" : "normal");
    });
  }

  // ---- Bienvenida (solo la primera vez) ----
  function iniciarBienvenida() {
    const d = $("#bienvenida-dialogo");
    if (!d || typeof d.showModal !== "function") return;
    const diapositivas = [...d.querySelectorAll(".diapositiva")];
    const puntos = [...d.querySelectorAll(".puntos span")];
    const siguiente = $("#bv-siguiente");
    let i = 0;

    function mostrar(n) {
      i = n;
      diapositivas.forEach((s, k) => s.classList.toggle("oculto", k !== n));
      puntos.forEach((p, k) => p.classList.toggle("activo", k === n));
      siguiente.textContent = n === diapositivas.length - 1 ? "Empezar" : "Siguiente";
    }
    function cerrar() {
      guardado.escribir("centinela-bienvenida", "vista");
      d.close();
    }
    function abrir() {
      mostrar(0);
      d.showModal();
      siguiente.focus();
    }

    siguiente.addEventListener("click", () => (i < diapositivas.length - 1 ? mostrar(i + 1) : cerrar()));
    $("#bv-saltar").addEventListener("click", cerrar);
    d.addEventListener("cancel", () => guardado.escribir("centinela-bienvenida", "vista"));
    const otraVez = $("#bv-abrir");
    if (otraVez) otraVez.addEventListener("click", abrir);
    if (!guardado.leer("centinela-bienvenida")) abrir();
  }

  // ---- Hoja de alerta: Escape, deslizar hacia abajo y vibración ----
  function iniciarAlerta() {
    const alerta = $("#alerta");
    const cerrar = $("#cerrar-alerta");
    if (!alerta || !cerrar) return;

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape" && !alerta.classList.contains("oculto")) cerrar.click();
    });

    let inicioY = null;
    alerta.addEventListener("touchstart", (e) => { inicioY = e.touches[0].clientY; }, { passive: true });
    alerta.addEventListener("touchmove", (e) => {
      if (inicioY === null) return;
      const dy = Math.max(0, e.touches[0].clientY - inicioY);
      alerta.style.setProperty("--arrastre", `${dy}px`);
    }, { passive: true });
    alerta.addEventListener("touchend", (e) => {
      if (inicioY === null) return;
      const dy = e.changedTouches[0].clientY - inicioY;
      inicioY = null;
      alerta.style.removeProperty("--arrastre");
      if (dy > 90) cerrar.click();
    });

    new MutationObserver(() => {
      const visible = !alerta.classList.contains("oculto");
      if (visible && ["alto", "critico"].includes(alerta.dataset.nivel) && navigator.vibrate) {
        navigator.vibrate(alerta.dataset.nivel === "critico" ? [180, 90, 180, 90, 180] : [180, 90, 180]);
      }
    }).observe(alerta, { attributes: true, attributeFilter: ["class"] });
  }

  // ---- Latido cuando cambia el nivel ----
  function iniciarNivel() {
    const nivel = $("#nivel");
    if (!nivel) return;
    new MutationObserver(() => {
      nivel.classList.remove("latido");
      void nivel.offsetWidth; // reinicia la animación
      nivel.classList.add("latido");
    }).observe(nivel, { attributes: true, attributeFilter: ["data-nivel"] });
    nivel.addEventListener("animationend", () => nivel.classList.remove("latido"));
  }

  // ---- Llevar a la vista la frase nueva, sin quitarle el foco a quien escribe ----
  function iniciarConversaciones() {
    for (const lista of document.querySelectorAll(".conversacion")) {
      new MutationObserver((cambios) => {
        const activo = document.activeElement;
        if (activo && (activo.tagName === "TEXTAREA" || activo.tagName === "INPUT")) return;
        const nueva = cambios.flatMap((c) => [...c.addedNodes]).filter((n) => n.nodeType === 1).pop();
        if (nueva && !lista.closest("details")) {
          nueva.scrollIntoView({ block: "nearest", behavior: sinMovimiento.matches ? "auto" : "smooth" });
        }
      }).observe(lista, { childList: true });
    }
  }

  // ---- Palabra clave familiar ----
  // Solo se recuerda SI la persona acordó una palabra con su familia; la palabra nunca se escribe en la app.
  const CLAVE_FAMILIAR = "centinela-palabra-clave";
  const SENALES_FAMILIA = ["finge_conocido", "emergencia_familiar", "voz_dudosa"];

  function tienePalabraClave() {
    return guardado.leer(CLAVE_FAMILIAR) === "acordada";
  }

  // Consejo extra para el aviso cuando alguien dice ser de la familia o cuenta una emergencia
  function consejoFamiliar(senales = []) {
    if (!senales.some((s) => SENALES_FAMILIA.includes(s.id || s))) return null;
    return tienePalabraClave()
      ? "Pregúntale la palabra clave que acordaron en familia. Si no la sabe, cuelga, aunque la voz suene igual."
      : "Cuelga y llama tú al número de siempre de esa persona. La voz se puede imitar con inteligencia artificial.";
  }

  function iniciarPalabraClave() {
    const casilla = $("#palabra-acordada");
    if (!casilla) return;
    casilla.checked = tienePalabraClave();
    const pintar = () => {
      $("#palabra-estado").textContent = casilla.checked
        ? "Listo. Cuando alguien diga ser de tu familia y pida plata, Centinela te recordará preguntarla."
        : "";
    };
    pintar();
    casilla.addEventListener("change", () => {
      guardado.escribir(CLAVE_FAMILIAR, casilla.checked ? "acordada" : "no");
      pintar();
    });
  }

  // ---- Contacto de confianza ----
  // Nombre y número quedan solo en este dispositivo. Centinela no envía nada: en un aviso crítico
  // muestra un botón que abre WhatsApp o los mensajes con el texto listo, y la persona decide si lo manda.
  const CLAVE_CONTACTO = "centinela-contacto";

  // Celular colombiano de 10 dígitos que empieza por 3, con o sin +57
  function normalizarCelular(texto) {
    let d = String(texto || "").replace(/\D/g, "");
    if (d.length === 12 && d.startsWith("57")) d = d.slice(2);
    return /^3\d{9}$/.test(d) ? d : null;
  }

  function leerContacto() {
    try {
      const c = JSON.parse(guardado.leer(CLAVE_CONTACTO) || "null");
      if (c && typeof c.nombre === "string" && normalizarCelular(c.telefono) && ["whatsapp", "sms"].includes(c.canal)) return c;
    } catch { /* dato dañado: se ignora */ }
    return null;
  }

  function textoParaContacto(contacto, motivo) {
    const saludo = contacto.nombre ? `Hola ${contacto.nombre}` : "Hola";
    const razon = motivo ? ` ${motivo.replace(/\.$/, "")}.` : "";
    return `${saludo}, Centinela marcó como posible estafa una llamada que estoy recibiendo.${razon} ¿Me puedes llamar? No voy a dar códigos, claves ni plata.`;
  }

  function enlaceContacto(contacto, motivo) {
    const texto = encodeURIComponent(textoParaContacto(contacto, motivo));
    const numero = "57" + normalizarCelular(contacto.telefono);
    return contacto.canal === "whatsapp" ? `https://wa.me/${numero}?text=${texto}` : `sms:+${numero}?body=${texto}`;
  }

  // Dentro de la app de Android, el contacto también queda en el celular para que el aviso de una llamada
  // riesgosa traiga "Llamar a …". CentinelaApp solo existe en la app y solo para el servidor configurado.
  function contarleALaApp() {
    const app = window.CentinelaApp;
    if (!app || typeof app.postMessage !== "function") return;
    const c = leerContacto();
    const mensaje = c ? { tipo: "contacto", nombre: c.nombre, telefono: normalizarCelular(c.telefono) } : { tipo: "contacto-quitado" };
    try { app.postMessage(JSON.stringify(mensaje)); } catch { /* la app no lo recibió: queda en la página */ }
  }

  // Botón del aviso: solo en riesgo crítico y si hay un contacto guardado
  function contactoParaAviso(nivel, motivo) {
    const c = leerContacto();
    if (nivel !== "critico" || !c) return null;
    return { href: enlaceContacto(c, motivo), texto: `Avisarle a ${c.nombre || "mi contacto"}` };
  }

  // Completa lo que comparten los avisos de todas las pantallas: palabra clave y contacto de confianza
  function completarAviso(alerta, decision, motivo) {
    const consejo = consejoFamiliar(decision.senales);
    const clave = alerta.querySelector(".alerta-clave");
    if (clave) {
      clave.textContent = consejo || "";
      clave.classList.toggle("oculto", !consejo);
    }
    const boton = alerta.querySelector(".alerta-contacto");
    if (boton) {
      const c = contactoParaAviso(decision.nivel, motivo);
      boton.classList.toggle("oculto", !c);
      if (c) {
        boton.href = c.href;
        boton.textContent = c.texto;
      } else {
        boton.removeAttribute("href");
      }
    }
  }

  function iniciarContacto() {
    const form = $("#form-contacto");
    if (!form) return;
    const estado = $("#contacto-estado");
    const quitar = $("#quitar-contacto");

    function pintar() {
      const c = leerContacto();
      quitar.classList.toggle("oculto", !c);
      $("#contacto-prueba").classList.toggle("oculto", !c);
      if (!c) {
        estado.textContent = "";
        return;
      }
      const n = normalizarCelular(c.telefono);
      estado.textContent = `Guardado: ${c.nombre || "Sin nombre"}, ${n.slice(0, 3)} ••• ${n.slice(6)}, por ${c.canal === "whatsapp" ? "WhatsApp" : "mensaje de texto"}.`;
      $("#contacto-prueba").href = enlaceContacto(c, "Esto es una prueba, no pasa nada");
      $("#contacto-nombre").value = c.nombre;
      $("#contacto-telefono").value = n;
      form.querySelector(`input[name="canal"][value="${c.canal}"]`).checked = true;
      $("#contacto-acepta").checked = true;
    }

    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const error = $("#contacto-error");
      const telefono = normalizarCelular($("#contacto-telefono").value);
      error.textContent = "";
      if (!telefono) {
        error.textContent = "Escribe un celular colombiano de 10 dígitos que empiece por 3.";
        $("#contacto-telefono").focus();
        return;
      }
      if (!$("#contacto-acepta").checked) {
        error.textContent = "Primero pregúntale a esa persona si está de acuerdo y marca la casilla.";
        $("#contacto-acepta").focus();
        return;
      }
      const canal = form.querySelector('input[name="canal"]:checked')?.value || "whatsapp";
      const nombre = $("#contacto-nombre").value.trim().slice(0, 30);
      guardado.escribir(CLAVE_CONTACTO, JSON.stringify({ nombre, telefono, canal }));
      contarleALaApp();
      pintar();
    });

    quitar.addEventListener("click", () => {
      try { localStorage.removeItem(CLAVE_CONTACTO); } catch { /* sin almacenamiento */ }
      contarleALaApp();
      form.reset();
      pintar();
    });
    pintar();
  }

  // ---- Pantallas dentro de una misma página: el inicio y un panel por cada herramienta ----
  // Cada panel se abre con su #ancla, así el botón Atrás del celular vuelve al inicio. Los enlaces
  // a una parte de un panel (#numero-titulo, #audio-titulo, #me-estafaron...) abren el panel que la tiene.
  function iniciarVistas() {
    const main = $("[data-vistas]");
    if (!main) return;
    const vistas = [...main.children].filter((n) => n.classList.contains("vista"));
    const inicio = vistas[0];
    let actual = null;
    let vinoDelInicio = false;

    function mostrar() {
      const id = decodeURIComponent(location.hash.slice(1));
      const destino = id ? document.getElementById(id) : null;
      const vista = destino ? vistas.find((v) => v.contains(destino)) : inicio;
      if (!vista) return; // un ancla fuera de los paneles, como "Saltar al contenido"
      const anterior = actual;
      for (const v of vistas) v.classList.toggle("oculto", v !== vista);
      actual = vista;
      vinoDelInicio = anterior === inicio && vista !== inicio;
      const plegable = destino && destino.closest("details");
      if (plegable) plegable.open = true;
      if (anterior === null && vista === inicio) return;
      const ubicar = () => {
        if (destino && destino !== vista && !destino.closest(".panel-cabeza")) destino.scrollIntoView({ block: "start" });
        else window.scrollTo({ top: 0, behavior: "instant" });
      };
      ubicar();
      // Al abrir la página con un #ancla, el navegador vuelve a mover la pantalla al terminar de cargar
      if (anterior === null && document.readyState !== "complete") addEventListener("load", ubicar, { once: true });
      if (anterior !== null) {
        const titulo = vista.querySelector(".panel-cabeza [tabindex='-1']") || vista;
        titulo.focus({ preventScroll: true });
      }
    }

    // "Volver" regresa en el historial si se llegó desde el inicio, para no apilar pantallas
    main.addEventListener("click", (e) => {
      if (e.target.closest(".volver") && vinoDelInicio) {
        e.preventDefault();
        history.back();
      }
    });
    // El logo y la pestaña de esta misma página vuelven al inicio sin recargar (no se pierde la conversación)
    document.addEventListener("click", (e) => {
      const a = e.target.closest("a[href]");
      if (!a || a.closest("[data-vistas]") || a.origin !== location.origin || a.hash) return;
      const misma = a.pathname === location.pathname || (a.pathname === "/" && location.pathname === "/index.html");
      if (!misma) return;
      e.preventDefault();
      if (actual !== inicio) location.hash = inicio.id;
      else window.scrollTo({ top: 0 });
    });
    addEventListener("hashchange", mostrar);
    mostrar();
  }

  window.Centinela = { consejoFamiliar, completarAviso, normalizarCelular, textoParaContacto };

  // ---- App instalable: el service worker solo guarda la interfaz, nunca respuestas de la API ----
  function registrarApp() {
    if ("serviceWorker" in navigator) navigator.serviceWorker.register("/sw.js").catch(() => {});
  }

  document.addEventListener("DOMContentLoaded", () => {
    registrarApp();
    iniciarVistas();
    iniciarPalabraClave();
    iniciarContacto();
    contarleALaApp();
    iniciarLetra();
    iniciarBienvenida();
    iniciarAlerta();
    iniciarNivel();
    iniciarConversaciones();
  });
})();
