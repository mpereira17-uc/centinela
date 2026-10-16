// El búho de Centinela: personaje y logo. Genera los SVG de frontend/buho/ con
//   node herramientas/buho.js
// Cuatro expresiones según el riesgo: tranquilo (saluda), atento (escucha), alerta (señala un aviso)
// y alarmado (levanta el ala para decir "detente"). Solo SVG puro, sin imágenes externas.
let N = 0;
const C = {
  blanco: '#FFFFFF', azul: '#1D5BD6', azulClaro: '#3B82FF', azulOsc: '#1446B8',
  noche: '#0B2A5B', celeste: '#E8F0FE', celeste2: '#7FB0FF', ambar: '#F5A524', rojo: '#D93B3B',
};
const f = (n) => Math.round(n * 100) / 100;

// Ala en coordenadas locales: hombro en (0,0), punta hacia +y, tres plumas redondeadas al final.
const ALA_DEDO = 'M-11 -2 C-18 16 -17 34 -11 44 Q-6 50 -2 47 L-2.5 64 Q-2 72 3 72 Q8 72 8.5 64 L8.5 46 C16 33 16 12 11 -2 Q0 -10 -11 -2 Z';
const ALA = 'M-11 -2 C-18 16 -18 38 -10 54 Q-6 63 -1 57 Q3 64 7 56 Q12 61 14 51 C18 34 16 12 11 -2 Q0 -10 -11 -2 Z';

function defs(id) {
  return `<defs>
  <radialGradient id="${id}c" cx="0.36" cy="0.26" r="0.86">
    <stop offset="0" stop-color="${C.azulClaro}"/><stop offset="0.55" stop-color="${C.azul}"/><stop offset="1" stop-color="${C.azulOsc}"/></radialGradient>
  <linearGradient id="${id}a" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="${C.azul}"/><stop offset="1" stop-color="${C.azulOsc}"/></linearGradient>
  <radialGradient id="${id}m" cx="0.5" cy="0.42" r="0.62">
    <stop offset="0.72" stop-color="${C.blanco}"/><stop offset="1" stop-color="${C.celeste}"/></radialGradient>
  <linearGradient id="${id}b" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="${C.blanco}"/><stop offset="1" stop-color="${C.celeste}"/></linearGradient>
  <radialGradient id="${id}i" cx="0.4" cy="0.3" r="0.8">
    <stop offset="0" stop-color="${C.azulClaro}"/><stop offset="1" stop-color="${C.azulOsc}"/></radialGradient>
  <radialGradient id="${id}s" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="${C.noche}" stop-opacity="0.22"/><stop offset="1" stop-color="${C.noche}" stop-opacity="0"/></radialGradient>
  </defs>`;
}

function ala(x, y, ang, espejo, id, forma = ALA) {
  const s = espejo ? ' scale(-1 1)' : '';
  return `<g transform="translate(${x} ${y})${s} rotate(${ang})"><path d="${forma}" fill="url(#${id}a)" stroke="url(#${id}a)" stroke-width="2" stroke-linejoin="round"/>
    <path d="M-3 8 Q-6 26 -3 42 M5 8 Q6 24 5 38" fill="none" stroke="${C.azulClaro}" stroke-width="2" stroke-linecap="round" opacity="0.55"/></g>`;
}

// Ala abierta de frente (gesto de "detente"): base redonda y cuatro plumas en abanico hacia arriba.
function palma(x, y, id, k = 1) {
  let p = '';
  [-33, -11, 11, 33].forEach((a, i) => {
    const l = i === 0 || i === 3 ? 26 : 31;
    p += `<g transform="rotate(${a})"><path d="M-5.5 -4 L-5.5 ${-l + 5} Q-5.5 ${-l - 3} 0 ${-l - 4} Q5.5 ${-l - 3} 5.5 ${-l + 5} L5.5 -4 Z" fill="url(#${id}a)"/>
      <path d="M0 -12 L0 ${-l + 4}" stroke="${C.azulClaro}" stroke-width="1.6" stroke-linecap="round" opacity="0.55"/></g>`;
  });
  return `<g transform="translate(${x} ${y}) scale(${k})">${p}<ellipse cx="0" cy="0" rx="15" ry="13" fill="url(#${id}a)"/></g>`;
}

// Párpado inferior "sonriente": medialuna blanca dentro del ojo.
function parpadoInf(cx, cy, r0) {
  const r = r0 + 1.2, d = r0 * 1.25, R = r0 * 0.95;
  const y0 = (r * r - R * R + d * d) / (2 * d), x0 = Math.sqrt(r * r - y0 * y0);
  return `<path d="M${f(cx - x0)} ${f(cy + y0)} A${f(r)} ${f(r)} 0 0 0 ${f(cx + x0)} ${f(cy + y0)} A${f(R)} ${f(R)} 0 0 0 ${f(cx - x0)} ${f(cy + y0)} Z" fill="${C.blanco}"/>`;
}

// Párpado superior: tapa el ojo por encima de la recta y = cy + c + s·(x - cx), con línea de borde.
function parpadoSup(cx, cy, r0, c, s) {
  const r = r0 + 1.2;
  const A = 1 + s * s, B = 2 * c * s, K = c * c - r * r;
  const disc = Math.sqrt(B * B - 4 * A * K);
  const x1 = (-B - disc) / (2 * A), x2 = (-B + disc) / (2 * A);
  const p1 = [cx + x1, cy + c + s * x1], p2 = [cx + x2, cy + c + s * x2];
  return `<path d="M${f(p1[0])} ${f(p1[1])} A${f(r)} ${f(r)} 0 ${c > 0 ? 1 : 0} 1 ${f(p2[0])} ${f(p2[1])} Z" fill="${C.blanco}"/>`;
}

// Ojo: iris con degradado, pupila, brillos. mirar = [dx,dy] en fracción del radio.
function ojo(cx, cy, r, id, o = {}) {
  const [mx, my] = o.mirar || [0, 0];
  const pr = r * (o.pupila || 0.56), b = o.brillo || 1;
  const px = cx + mx * r * 0.32, py = cy + my * r * 0.32;
  let s = `<circle cx="${cx}" cy="${cy}" r="${r}" fill="url(#${id}i)"/>
    <circle cx="${f(px)}" cy="${f(py)}" r="${f(pr)}" fill="${C.noche}"/>
    <circle cx="${f(px - r * 0.27)}" cy="${f(py - r * 0.3)}" r="${f(r * 0.26 * b)}" fill="${C.blanco}"/>
    <circle cx="${f(px + r * 0.3)}" cy="${f(py + r * 0.28)}" r="${f(r * 0.1)}" fill="${C.blanco}"/>`;
  if (o.feliz) s += parpadoInf(cx, cy, r);
  if (o.sup) s += parpadoSup(cx, cy, r, o.sup[0], o.sup[1]);
  return s;
}

const SILUETA = 'M100 41 C88 41 78 39 71 35 Q67 32 64 27 Q61 34 58 37 Q54 30 50 22 Q44 36 46 52 Q46 62 46 72 C31 96 29 144 48 168 C61 185 79 190 100 190 C121 190 139 185 152 168 C171 144 169 96 154 72 Q154 62 154 52 Q156 36 150 22 Q146 30 142 37 Q139 34 136 27 Q133 32 129 35 C122 39 112 41 100 41 Z';

function cuerpo(id) {
  return `<ellipse cx="100" cy="193" rx="46" ry="5.5" fill="url(#${id}s)"/>
  <path d="${SILUETA}" fill="url(#${id}c)" stroke="url(#${id}c)" stroke-width="7" stroke-linejoin="round"/>
  <path d="M53 30 Q51 40 52 50 M147 30 Q149 40 148 50" fill="none" stroke="${C.celeste2}" stroke-width="2.4" stroke-linecap="round" opacity="0.6"/>
  <path d="M68 146 C68 130 84 126 100 126 C116 126 132 130 132 146 C132 170 118 184 100 184 C82 184 68 170 68 146 Z" fill="url(#${id}b)"/>
  <path d="M84 146 q4 5 8 0 M100 146 q4 5 8 0 M92 158 q4 5 8 0 M108 158 q4 5 8 0 M76 158 q4 5 8 0 M84 170 q4 5 8 0 M100 170 q4 5 8 0"
    fill="none" stroke="${C.celeste2}" stroke-width="2.4" stroke-linecap="round"/>
  <ellipse cx="100" cy="128" rx="34" ry="7" fill="url(#${id}s)"/>
  <path d="M100 60 C90 50 56 50 52 82 C49 106 72 122 100 126 C128 122 151 106 148 82 C144 50 110 50 100 60 Z" fill="url(#${id}m)"/>`;
}

const patas = [83, 117].map((x) => [-5.5, 0, 5.5].map((d) => `<ellipse cx="${x + d}" cy="${189 + (d ? 0 : 1)}" rx="3.4" ry="4.2" fill="${C.celeste2}"/>`).join('')).join('');

function pico(abierto) {
  if (abierto) return `<path d="M92 101 Q100 97 108 101 Q105 108 100 110 Q95 108 92 101 Z" fill="${C.celeste2}"/>
    <path d="M94.5 110 Q100 108 105.5 110 Q104 118 100 120 Q96 118 94.5 110 Z" fill="${C.noche}"/>`;
  return `<path d="M92 101 Q100 97 108 101 Q105 112 100 117 Q95 112 92 101 Z" fill="${C.celeste2}"/>
    <path d="M95 101.5 Q100 99.5 105 101.5 Q102 104 100 104.5 Q98 104 95 101.5 Z" fill="${C.blanco}" opacity="0.6"/>`;
}

const ceja = (d, w = 5) => `<path d="${d}" fill="none" stroke="${C.noche}" stroke-width="${w}" stroke-linecap="round" stroke-linejoin="round"/>`;

function svg(expr = 'tranquilo') {
  const id = 'cc' + (++N) + '_';
  let atras = '', frente = '', cara = '', extra = '';
  const reposoIzq = ala(48, 110, 8, true, id), reposoDer = ala(152, 110, 8, false, id);
  if (expr === 'tranquilo') {
    frente = reposoIzq + ala(148, 114, -150, false, id);
    cara = ojo(79, 86, 16, id, { feliz: true }) + ojo(121, 86, 16, id, { feliz: true }) +
      `<ellipse cx="68" cy="106" rx="8" ry="4.5" fill="${C.celeste2}" opacity="0.4"/><ellipse cx="132" cy="106" rx="8" ry="4.5" fill="${C.celeste2}" opacity="0.4"/>` +
      ceja('M66 64 Q78 57 90 63') + ceja('M110 63 Q122 57 134 64') + pico(false);
  } else if (expr === 'atento') {
    frente = reposoDer + ala(54, 118, 190, true, id);
    extra = `<g fill="none" stroke-width="5" stroke-linecap="round">
      <path d="M25 54 Q18 66 25 78" stroke="${C.azul}" opacity="0.75"/><path d="M13 45 Q2 66 13 87" stroke="${C.celeste2}"/></g>`;
    cara = ojo(79, 86, 17, id, { mirar: [-0.7, -0.25] }) + ojo(121, 86, 17, id, { mirar: [-0.7, -0.25] }) +
      ceja('M65 59 Q78 50 91 56') + ceja('M110 62 Q122 59 134 62') + pico(false);
  } else if (expr === 'alerta') {
    frente = reposoIzq + ala(148, 112, 196, false, id, ALA_DEDO);
    extra = `<g transform="translate(170 26) scale(1.25)"><path d="M0 -14 Q3 -14 5 -10 L15 8 Q17 13 12 13 L-12 13 Q-17 13 -15 8 L-5 -10 Q-3 -14 0 -14 Z" fill="${C.ambar}"/>
      <rect x="-2.2" y="-6" width="4.4" height="11" rx="2.2" fill="${C.noche}"/><circle cx="0" cy="9" r="2.4" fill="${C.noche}"/></g>`;
    cara = ojo(79, 88, 16, id, { pupila: 0.5, mirar: [0.35, -0.1], sup: [-9.5, 0.2] }) + ojo(121, 88, 16, id, { pupila: 0.5, mirar: [0.35, -0.1], sup: [-9.5, -0.2] }) +
      ceja('M64 68 Q78 65 91 72') + ceja('M109 72 Q122 65 136 68') + pico(false);
  } else {
    // alarmado: ala abierta de frente en gesto de "detente", con aro rojo. Cejas de preocupación, no de enojo.
    frente = reposoIzq + `<path d="M146 106 C157 104 162 96 163 86 L177 86 C177 106 166 124 148 132 Z" fill="url(#${id}a)" stroke="url(#${id}a)" stroke-width="3" stroke-linejoin="round"/>` +
      `<circle cx="170" cy="68" r="24" fill="none" stroke="${C.rojo}" stroke-width="6"/>` + palma(170, 80, id, 0.72);
    cara = ojo(79, 88, 17, id, { pupila: 0.44, brillo: 0.8 }) + ojo(121, 88, 17, id, { pupila: 0.44, brillo: 0.8 }) +
      ceja('M62 70 Q75 66 90 57', 5.5) + ceja('M110 57 Q125 66 138 70', 5.5) + pico(true);
  }
  return `<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">${defs(id)}${extra}${atras}${cuerpo(id)}${patas}${cara}${frente}</svg>`;
}

function icono() {
  const id = 'cci' + (++N) + '_';
  return `<svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg"><defs>
  <linearGradient id="${id}f" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${C.azulClaro}"/><stop offset="1" stop-color="${C.azulOsc}"/></linearGradient>
  <radialGradient id="${id}m" cx="0.5" cy="0.45" r="0.62"><stop offset="0.75" stop-color="${C.blanco}"/><stop offset="1" stop-color="${C.celeste}"/></radialGradient>
  <radialGradient id="${id}i" cx="0.4" cy="0.3" r="0.8"><stop offset="0" stop-color="${C.azulClaro}"/><stop offset="1" stop-color="${C.azulOsc}"/></radialGradient>
  </defs><rect width="100" height="100" rx="23" fill="url(#${id}f)"/>
  <path d="M50 27 C43 27 37 26 33 24 Q30 22 28 17.5 Q26.5 22 24.5 24 Q22 19.5 19.5 14 Q16 23 17 33 Q15 47 17 61 Q21 85 50 87 Q79 85 83 61 Q85 47 83 33 Q84 23 80.5 14 Q78 19.5 75.5 24 Q73.5 22 72 17.5 Q70 22 67 24 C63 26 57 27 50 27 Z" fill="url(#${id}m)" stroke="url(#${id}m)" stroke-width="3" stroke-linejoin="round"/>
  <circle cx="37.5" cy="56" r="11.5" fill="url(#${id}i)"/><circle cx="62.5" cy="56" r="11.5" fill="url(#${id}i)"/>
  <circle cx="37.5" cy="56" r="6.2" fill="${C.noche}"/><circle cx="62.5" cy="56" r="6.2" fill="${C.noche}"/>
  <circle cx="34.5" cy="52.5" r="3.1" fill="#fff"/><circle cx="59.5" cy="52.5" r="3.1" fill="#fff"/>
  <path d="M27 42 Q36 35.5 45.5 41 M54.5 41 Q64 35.5 73 42" fill="none" stroke="${C.noche}" stroke-width="3.8" stroke-linecap="round"/>
  <path d="M45 68 Q50 66 55 68 Q53 74 50 77 Q47 74 45 68 Z" fill="${C.celeste2}"/></svg>`;
}

const fs = require('fs');
const path = require('path');
const destino = path.join(__dirname, '..', 'frontend', 'buho');
fs.mkdirSync(destino, { recursive: true });
for (const expr of ['tranquilo', 'atento', 'alerta', 'alarmado']) {
  fs.writeFileSync(path.join(destino, `${expr}.svg`), svg(expr) + '\n');
}
fs.writeFileSync(path.join(destino, 'icono.svg'), icono() + '\n');
console.log('Búho listo en', destino);
