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

  document.addEventListener("DOMContentLoaded", () => {
    iniciarLetra();
    iniciarBienvenida();
    iniciarAlerta();
    iniciarNivel();
    iniciarConversaciones();
  });
})();
