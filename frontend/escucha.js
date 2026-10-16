"use strict";

// Escucha por trozos que terminan en las pausas de quien habla. Así cada trozo lleva frases completas
// ("dícteme el código que le llegó" no queda partido en dos) y se analiza apenas la persona hace una pausa,
// en vez de esperar un tiempo fijo. Los silencios no se envían. Lo usan la llamada de prueba y el modo
// acompañante. El audio solo vive en memoria hasta enviarse; no se guarda.
//
// Si el navegador no deja medir el volumen, o el volumen llega en cero absoluto (pasa con algunos audios
// de llamada en ciertos navegadores), vuelve a trozos fijos de unos segundos, como antes.
//
// Mientras Centinela dice un aviso en voz alta, lo que se graba se descarta (silenciar), para que no
// analice su propia voz como si fuera la de quien llama.

(function () {
  const MIN_TROZO = 1200;      // ms: menos que esto casi nunca es una frase
  const MAX_TROZO = 8000;      // ms: aunque no haya pausa, se analiza a los 8 segundos
  const PAUSA = 700;           // ms de silencio que cierran una frase
  const SIN_VOZ = 4000;        // ms de silencio que se descartan sin enviar
  const FIJO = 6000;           // ms por trozo cuando no se puede medir el volumen
  const CADA = 50;             // ms entre mediciones
  const UMBRAL_MINIMO = 0.012; // volumen (RMS) por debajo del cual nunca es voz

  function tipoDeAudio() {
    if (typeof MediaRecorder !== "function") return null;
    return ["audio/webm;codecs=opus", "audio/webm", "audio/mp4", "audio/ogg"].find((t) => MediaRecorder.isTypeSupported(t)) || "";
  }

  function nombreDeArchivo(blob) {
    return blob.type.includes("mp4") ? "trozo.mp4" : blob.type.includes("ogg") ? "trozo.ogg" : "trozo.webm";
  }

  // opciones: { alTrozo(blob, conVoz), alVolumen(0..1, hayVoz), alCambiarModo(modo) }
  function escuchar(flujo, opciones) {
    const tipo = tipoDeAudio();
    if (tipo === null) return null;
    const estado = { activo: true, actual: null, medidor: null, ctx: null, modo: "pausas", mudoHasta: 0, reloj: null };

    function nuevoTrozo() {
      const partes = [];
      const recorder = new MediaRecorder(flujo, tipo ? { mimeType: tipo } : undefined);
      const trozo = { recorder, inicio: performance.now(), hayVoz: false, ultimaVoz: 0, enviar: false, mudo: performance.now() < estado.mudoHasta };
      recorder.addEventListener("dataavailable", (e) => { if (e.data.size) partes.push(e.data); });
      recorder.addEventListener("stop", () => {
        const audio = new Blob(partes, { type: recorder.mimeType || tipo || "audio/webm" });
        if (trozo.enviar && audio.size > 1000) opciones.alTrozo(audio);
      });
      recorder.start();
      return trozo;
    }

    // El siguiente trozo empieza antes de cerrar el anterior, para no perder la primera sílaba
    function cortar(enviar) {
      const viejo = estado.actual;
      estado.actual = estado.activo ? nuevoTrozo() : null;
      if (viejo && viejo.recorder.state === "recording") {
        viejo.enviar = enviar && !viejo.mudo;
        viejo.recorder.stop();
      }
    }

    function modoFijo() {
      estado.modo = "fijo";
      opciones.alCambiarModo?.("fijo");
      clearInterval(estado.medidor);
      estado.medidor = setInterval(() => { if (estado.activo) cortar(true); }, FIJO);
    }

    function medir() {
      let ctx;
      try {
        const Contexto = window.AudioContext || window.webkitAudioContext;
        ctx = new Contexto();
      } catch {
        return false;
      }
      estado.ctx = ctx;
      ctx.resume?.().catch(() => {});
      const analizador = ctx.createAnalyser();
      analizador.fftSize = 1024;
      ctx.createMediaStreamSource(flujo).connect(analizador);
      const muestras = new Float32Array(analizador.fftSize);
      let fondo = 0.005;        // ruido de fondo, se ajusta solo
      let ceroDesde = performance.now();

      estado.medidor = setInterval(() => {
        if (!estado.activo || !estado.actual) return;
        const ahora = performance.now();
        analizador.getFloatTimeDomainData(muestras);
        let suma = 0;
        for (const m of muestras) suma += m * m;
        const rms = Math.sqrt(suma / muestras.length);

        // Cero absoluto durante 3 segundos: el navegador no entrega el audio para medirlo
        if (rms > 0 || ctx.state !== "running") ceroDesde = ahora;
        else if (ahora - ceroDesde > 3000) { modoFijo(); return; }

        const umbral = Math.max(UMBRAL_MINIMO, fondo * 3);
        const hayVoz = rms > umbral;
        if (!hayVoz) fondo = fondo * 0.97 + rms * 0.03;
        opciones.alVolumen?.(Math.min(1, rms / 0.15), hayVoz);

        const t = estado.actual;
        const dura = ahora - t.inicio;
        if (hayVoz) {
          t.hayVoz = true;
          t.ultimaVoz = ahora;
        }
        if (t.hayVoz && ahora - t.ultimaVoz >= PAUSA && dura >= MIN_TROZO) cortar(true);
        else if (dura >= MAX_TROZO) cortar(t.hayVoz);
        else if (!t.hayVoz && dura >= SIN_VOZ) cortar(false);
      }, CADA);
      return true;
    }

    estado.actual = nuevoTrozo();
    if (!medir()) modoFijo();

    return {
      get modo() { return estado.modo; },
      // Descarta lo que se grabe durante ms (por ejemplo, mientras el celular dice un aviso)
      silenciar(ms) {
        if (!estado.activo) return;
        estado.mudoHasta = Math.max(estado.mudoHasta, performance.now() + ms);
        if (estado.actual) estado.actual.mudo = true;
        clearTimeout(estado.reloj);
        // Al terminar, se empieza un trozo limpio en vez de esperar al siguiente corte
        estado.reloj = setTimeout(() => { if (estado.activo && estado.actual?.mudo) cortar(false); }, estado.mudoHasta - performance.now());
      },
      detener() {
        if (!estado.activo) return;
        estado.activo = false;
        clearInterval(estado.medidor);
        clearTimeout(estado.reloj);
        // Al colgar ya no se analiza nada más
        const t = estado.actual;
        if (t && t.recorder.state === "recording") t.recorder.stop();
        estado.actual = null;
        estado.ctx?.close().catch(() => {});
      },
    };
  }

  window.CentinelaEscucha = { escuchar, nombreDeArchivo, disponible: () => tipoDeAudio() !== null };
})();
