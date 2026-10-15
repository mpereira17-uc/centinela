"use strict";

// Todo el texto se inserta con textContent, nunca como HTML (modelo de amenazas, A5).

const $ = (sel) => document.querySelector(sel);
let grupos = [];

function sinTildes(texto) {
  return texto.normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase();
}

function enlace(href, texto, clase) {
  const a = document.createElement("a");
  a.href = href;
  a.textContent = texto;
  a.className = clase;
  if (href.startsWith("http")) { a.target = "_blank"; a.rel = "noopener noreferrer"; }
  return a;
}

function pintarDirectorio(filtro = "") {
  const buscado = sinTildes(filtro.trim());
  const lista = $("#directorio-lista");
  lista.replaceChildren();
  let total = 0;
  for (const g of grupos) {
    const entradas = g.entradas.filter((e) => !buscado || sinTildes(`${e.nombre} ${e.para || ""}`).includes(buscado));
    if (!entradas.length) continue;
    total += entradas.length;
    const titulo = document.createElement("h3");
    titulo.className = "subtitulo";
    titulo.textContent = g.titulo;
    lista.append(titulo);
    if (g.consejo) {
      const c = document.createElement("p");
      c.className = "ayuda";
      c.textContent = g.consejo;
      lista.append(c);
    }
    const ul = document.createElement("ul");
    ul.className = "directorio";
    for (const e of entradas) {
      const li = document.createElement("li");
      const nombre = document.createElement("strong");
      nombre.textContent = e.nombre;
      li.append(nombre);
      if (e.para) {
        const p = document.createElement("span");
        p.textContent = e.para;
        li.append(p);
      }
      const acciones = document.createElement("div");
      acciones.className = "fila-acciones";
      if (e.telefono) acciones.append(enlace(`tel:${e.telefono}`, `Llamar al ${e.telefono}`, "boton-principal"));
      if (e.web) acciones.append(enlace(e.web, "Página oficial", "boton-secundario"));
      li.append(acciones);
      ul.append(li);
    }
    lista.append(ul);
  }
  $("#directorio-estado").textContent = buscado && !total
    ? "No está en la lista. Busca el canal oficial en tu factura, tu tarjeta o la aplicación de la entidad."
    : "";
}

async function cargarDirectorio() {
  try {
    const r = await fetch("/directorio");
    if (!r.ok) throw new Error();
    const datos = await r.json();
    grupos = datos.grupos;
    $("#directorio-fecha").textContent = `Lista revisada el ${datos.actualizado}. Si un número cambió, la página oficial tiene el correcto.`;
    pintarDirectorio();
  } catch {
    $("#directorio-estado").textContent = "No pudimos cargar el directorio. Mientras tanto: emergencias 123, extorsión 165 (GAULA).";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  cargarDirectorio();
  $("#buscar-entidad").addEventListener("input", (e) => pintarDirectorio(e.target.value));
  if (location.hash) document.querySelector(location.hash)?.scrollIntoView();
});

// ---------- Me estafaron, ¿qué hago? ----------
// Cada paso dice para qué situaciones aplica; el orden de la lista es el orden de urgencia.
const PASOS = [
  { id: "cortar", para: ["amenaza"], titulo: "No pagues ni sigas hablando",
    detalle: "Cuelga, no envíes plata y guarda los mensajes, audios y números. Llama al 165 (GAULA): atienden extorsiones las 24 horas.",
    enlace: ["tel:165", "Llamar al 165"] },
  { id: "banco", para: ["codigo", "tarjeta", "transferencia"], titulo: "Llama a tu banco ya mismo",
    detalle: "Usa el número del respaldo de tu tarjeta o el de la aplicación oficial. Pide bloquear la tarjeta o la cuenta y pregunta si la operación se puede detener o reversar. Mientras más rápido, más posibilidades.",
    enlace: ["#directorio", "Buscar el canal oficial"] },
  { id: "billetera", para: ["transferencia"], titulo: "Si fue por Nequi, Daviplata u otra billetera, repórtalo en su aplicación",
    detalle: "Busca la opción de ayuda o de reportar una transacción dentro de la app oficial. Anota la hora, el valor y el número o la llave a la que enviaste." },
  { id: "desconectar", para: ["aplicacion"], titulo: "Desconecta el celular de internet y desinstala la aplicación",
    detalle: "Apaga los datos y el wifi. Desinstala la aplicación que te hicieron poner (AnyDesk, TeamViewer o cualquiera desconocida). Si no puedes, lleva el celular a revisión antes de abrir tu banco." },
  { id: "whatsapp", para: ["whatsapp"], titulo: "Recupera tu WhatsApp",
    detalle: "Abre WhatsApp y vuelve a registrar tu número: eso cierra la sesión del estafador. Luego activa la verificación en dos pasos en Ajustes > Cuenta. Avísales a tus contactos que no respondan a pedidos de plata desde tu número." },
  { id: "claves", para: ["codigo", "tarjeta", "aplicacion", "whatsapp"], titulo: "Cambia tus claves desde un equipo seguro",
    detalle: "Cambia la clave del banco, del correo y de las redes. Si instalaste una aplicación, hazlo desde otro celular o computador. Activa la verificación en dos pasos donde se pueda." },
  { id: "datos", para: ["datos"], titulo: "Vigila que no abran créditos a tu nombre",
    detalle: "Con tu cédula pueden intentar suplantarte. Revisa tu historial en las centrales de riesgo (Datacrédito o TransUnion) y desconfía de llamadas que ya conocen tus datos." },
  { id: "denunciar", para: ["codigo", "whatsapp", "tarjeta", "transferencia", "aplicacion", "datos", "amenaza"], titulo: "Denuncia",
    detalle: "Centinela te arma un resumen con la evidencia. Puedes denunciar por internet en ADenunciar, llamar al 122 de la Fiscalía o ir a una estación. Pide el número de la denuncia: el banco te lo puede pedir.",
    enlace: ["/#denuncia", "Preparar la denuncia"] },
  { id: "reportar", para: ["codigo", "whatsapp", "tarjeta", "transferencia", "aplicacion", "datos", "amenaza"], titulo: "Reporta el número en Centinela",
    detalle: "Así la próxima persona que reciba una llamada de ese número recibe un aviso.",
    enlace: ["/#numero-titulo", "Reportar el número"] },
  { id: "familia", para: ["codigo", "whatsapp", "tarjeta", "transferencia", "aplicacion", "datos", "amenaza"], titulo: "Cuéntaselo a alguien de confianza",
    detalle: "Los estafadores a veces vuelven a llamar fingiendo ser la policía o el banco para 'ayudarte a recuperar la plata'. Es otra estafa: nadie legítimo te cobra por recuperarla." },
];
const CLAVE_HECHOS = "centinela-pasos-hechos";

function leerHechos() {
  try { return new Set(JSON.parse(localStorage.getItem(CLAVE_HECHOS) || "[]")); } catch { return new Set(); }
}

function guardarHechos(hechos) {
  try { localStorage.setItem(CLAVE_HECHOS, JSON.stringify([...hechos])); } catch { /* sin almacenamiento */ }
}

function pintarPasos() {
  const elegidas = [...document.querySelectorAll("#situaciones input:checked")].map((i) => i.value);
  const hechos = leerHechos();
  const lista = $("#pasos");
  lista.replaceChildren();
  for (const paso of PASOS.filter((p) => p.para.some((s) => elegidas.includes(s)))) {
    const li = document.createElement("li");
    li.dataset.hecho = hechos.has(paso.id) ? "si" : "no";
    const marca = document.createElement("label");
    marca.className = "paso-marca";
    const caja = document.createElement("input");
    caja.type = "checkbox";
    caja.checked = hechos.has(paso.id);
    caja.addEventListener("change", () => {
      const actuales = leerHechos();
      caja.checked ? actuales.add(paso.id) : actuales.delete(paso.id);
      guardarHechos(actuales);
      li.dataset.hecho = caja.checked ? "si" : "no";
    });
    const titulo = document.createElement("strong");
    titulo.textContent = paso.titulo;
    marca.append(caja, titulo);
    const detalle = document.createElement("p");
    detalle.textContent = paso.detalle;
    li.append(marca, detalle);
    if (paso.enlace) li.append(enlace(paso.enlace[0], paso.enlace[1], "boton-secundario"));
    lista.append(li);
  }
  $("#pasos-vacio").classList.toggle("oculto", elegidas.length > 0);
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("#situaciones input").forEach((i) => i.addEventListener("change", pintarPasos));
});
