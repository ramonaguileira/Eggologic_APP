// La chacra: el dibujo de fondo, los objetos que hacen de botones y las gallinas que andan solas.
// No hay motor de juegos: cada cosa es un elemento de la página, ubicado en "píxeles de dibujo".
// Un píxel de dibujo mide --u en la pantalla (4 px en un celular común).

const app = document.getElementById("app");
const cosas = document.getElementById("cosas");
const chacra = document.getElementById("chacra");

let reloj = null;
let gallinas = [];
let bicho = null;
let zona = null;
let proximoBicho = 0;
// Dónde va la pila de maples, y qué había apilado la última vez.
let lugarDeLaPila = null;
let apilado = "";

const azar = (desde, hasta) => desde + Math.random() * (hasta - desde);

// Crea un elemento ubicado en la chacra. x, y, ancho y alto van en píxeles de dibujo.
function cosa(imagen, ancho, alto, x, y, etiqueta = "div") {
  const el = document.createElement(etiqueta);
  el.className = "cosa";
  el.style.backgroundImage = `url("arte/${imagen}.png")`;
  el.style.setProperty("--w", ancho);
  el.style.setProperty("--h", alto);
  mover(el, x, y);
  cosas.append(el);
  return el;
}

function mover(el, x, y) {
  el.style.setProperty("--x", Math.round(x));
  el.style.setProperty("--y", Math.round(y));
  el.style.zIndex = Math.round(y + Number(el.style.getPropertyValue("--h")));
}

// Muestra el cuadro número `n` de una tira de animación.
function cuadro(el, n) {
  el.style.backgroundPositionX = `calc(${-n} * var(--w) * var(--u))`;
}

function boton(imagen, ancho, alto, x, y, cartel, panel, alAbrir) {
  const el = cosa(imagen, ancho, alto, x, y, "button");
  el.innerHTML = `<span class="cartel">${cartel}</span>`;
  el.setAttribute("aria-label", cartel);
  // Con este nombre lo encuentra el recorrido de la primera vez (js/tour.js).
  el.dataset.tour = panel;
  el.addEventListener("click", () => alAbrir(panel));
  return el;
}

function globo(sobre, imagen, ancho, alto) {
  const el = document.createElement("img");
  el.src = `arte/${imagen}.png`;
  el.className = "globo pixel";
  el.style.width = `calc(${ancho} * var(--u))`;
  el.style.height = `calc(${alto} * var(--u))`;
  sobre.append(el);
  setTimeout(() => el.remove(), 1000);
}

export function esDeNoche() {
  const hora = Number(
    new Intl.DateTimeFormat("es-UY", { hour: "numeric", hour12: false, timeZone: "America/Montevideo" }).format(new Date())
  );
  return hora >= 20 || hora < 6;
}

// Arma la chacra entera. Se vuelve a llamar cuando cambian las gallinas o el tamaño de la pantalla.
// `sueltos` son los huevos recién puestos que esperan en el pasto; al tocar uno se llama a alJuntar.
export function armar(estado, alAbrir, sueltos = 0, alJuntar = () => {}) {
  clearInterval(reloj);
  cosas.innerHTML = "";
  const u = Math.max(3, Math.floor(app.clientWidth / 96));
  app.style.setProperty("--u", `${u}px`);
  const ancho = app.clientWidth / u;
  const alto = app.clientHeight / u;
  const horizonte = alto * 0.42;
  const noche = esDeNoche();
  chacra.className = noche ? "noche" : "dia";

  // Cielo.
  cosa("sol", 13, 12, ancho - 24, 20).classList.add("de-dia");
  cosa("luna", 9, 10, ancho - 22, 20).classList.add("de-noche");
  cosa("nube", 20, 6, 0, 30).classList.add("de-dia", "nube");
  const nube = cosa("nube", 20, 6, 0, 46);
  nube.classList.add("de-dia", "nube");
  nube.style.animationDelay = "-50s";
  for (let i = 0; i < 16; i++) {
    const estrella = document.createElement("i");
    estrella.className = "estrella de-noche";
    estrella.style.left = `${azar(2, 98)}%`;
    estrella.style.top = `${azar(8, 36)}%`;
    estrella.style.animationDelay = `${azar(0, 2)}s`;
    cosas.append(estrella);
  }

  // Fondo: el cerco a lo ancho, un árbol y pastitos.
  const cerco = cosa("cerco", ancho, 13, 0, horizonte - 9);
  cerco.style.backgroundRepeat = "repeat-x";
  cosa("arbol", 20, 20, ancho * 0.36, horizonte - 17);
  for (let i = 0; i < 9; i++) cosa("mata", 8, 3, azar(2, ancho - 10), azar(horizonte + 10, alto - 8)).classList.add("adorno");
  for (let i = 0; i < 4; i++) cosa("flor", 5, 6, azar(2, ancho - 8), azar(horizonte + 12, alto - 10)).classList.add("adorno");

  // Los botones son cosas de la chacra, cada una con su cartelito.
  boton("granero", 28, 24, 4, horizonte - 16, "Tienda", "tienda", alAbrir);
  const gallinero = boton("gallinero", 22, 18, ancho - 26, horizonte - 9, "Gallinas", "gallinas", alAbrir);
  if (!estado.gallinas.length) {
    // Sin gallinas todavía, el cartel del gallinero invita a adoptar.
    const cartel = gallinero.querySelector(".cartel");
    cartel.textContent = "¡Adoptá!";
    cartel.classList.add("llama");
  }
  boton("casita", 22, 22, ancho * 0.62 - 11, horizonte - 17, "Mi cuenta", "cuenta", alAbrir);
  const nido = boton("nido", 18, 8, 12, alto - 30, "Canjear huevos", "huevos", alAbrir);
  boton("brote", 16, 16, ancho / 2 - 8, alto - 36, "Impacto", "impacto", alAbrir);
  const balde = boton("balde", 16, 16, ancho - 24, alto - 38, "Residuos", "residuos", alAbrir);
  const hayResiduosEnCamino = estado.levantes.some((levante) => levante.paso === "pedido");
  cuadro(balde, hayResiduosEnCamino ? 1 : 0);
  lugarDeLaPila = { x: 12, y: alto - 37, nido, minimo: estado.huevos.minimo, alAbrir };
  apilado = "";
  apilar(estado.huevos.para_pedir - sueltos);

  // Comida y agua: son solo cariño. Las gallinas van a comer, pero no cambia la producción.
  const comedero = cosa("comedero", 16, 5, ancho * 0.22, horizonte + 30, "button");
  const bebedero = cosa("bebedero", 12, 5, ancho * 0.66, horizonte + 34, "button");
  comedero.setAttribute("aria-label", "Darles de comer");
  bebedero.setAttribute("aria-label", "Darles agua");
  comedero.addEventListener("click", () => llamar(comedero));
  bebedero.addEventListener("click", () => llamar(bebedero));

  // Por dónde andan las gallinas.
  zona = { x1: 4, x2: ancho - 20, y1: horizonte + 8, y2: alto - 62 };
  for (let i = 0; i < sueltos; i++) huevoSuelto(nido, alJuntar);
  gallinas = estado.gallinas
    .filter((gallina) => gallina.estado === "activa")
    .map((gallina) => crearGallina(gallina, noche));
  bicho = null;
  proximoBicho = azar(6000, 14000);

  // La chacra vacía igual tiene vida: un pajarito que cruza y un caracol que camina.
  const pajarito = cosa("pajarito", 12, 8, -20, 60);
  const caracol = cosa("caracol", 12, 8, -14, alto - 20);
  let tiempo = 0;
  const TIC = 120;
  reloj = setInterval(() => {
    tiempo += TIC;
    if (!noche) {
      const vuelo = (tiempo / 60) % (ancho + 300);
      mover(pajarito, vuelo - 20, 58 + Math.sin(tiempo / 500) * 4);
      cuadro(pajarito, Math.floor(tiempo / 240) % 2);
    }
    const paso = (tiempo / 900) % (ancho + 60);
    mover(caracol, paso - 14, alto - 20);
    cuadro(caracol, Math.floor(tiempo / 720) % 2);
    if (!noche) {
      gallinas.forEach((gallina) => vivir(gallina, TIC));
      bichos(TIC);
    }
  }, TIC);
}

// Los huevos juntados, a la vista sin abrir nada: en el nido los del maple que se está llenando
// y, arriba, los maples completos. Cada 15 es un maple; dos de 15 se atan en uno de 30.
// Se llama al armar la chacra y cada vez que se junta un huevo.
export function apilar(huevos) {
  if (!lugarDeLaPila) return;
  const { x, y, nido, minimo, alAbrir } = lugarDeLaPila;
  cosas.querySelectorAll(".pila").forEach((el) => el.remove());
  huevos = Math.max(huevos, 0);
  const de30 = Math.floor(huevos / 30);
  const de15 = Math.floor((huevos % 30) / 15);
  const sueltosEnElNido = huevos % 15;

  for (let i = 0; i < Math.ceil(sueltosEnElNido / 5); i++) {
    const huevo = cosa("huevo", 7, 8, x + 2 + i * 5, y + 1);
    huevo.classList.add("pila");
    huevo.style.pointerEvents = "none";
  }
  // En pantalla entran 4 maples de 30; si hay más, el cartelito dice cuántos.
  const piezas = [...Array(Math.min(de30, 4)).fill(["maple-30", 8]), ...Array(de15).fill(["maple-15", 5])];
  let base = y - 1;
  let ultima = null;
  for (const [imagen, altura] of piezas) {
    base -= altura - 1;
    ultima = cosa(imagen, 18, altura, x, base, "button");
    ultima.classList.add("pila");
    ultima.setAttribute("aria-label", "Canjear huevos");
    ultima.addEventListener("click", () => alAbrir("huevos"));
  }
  if (ultima) {
    const cuenta = [de30 ? `${de30} de 30` : "", de15 ? "1 de 15" : ""].filter(Boolean).join(" + ");
    ultima.insertAdjacentHTML("beforeend", `<span class="cartel cuenta">${cuenta}</span>`);
    // Cuando la pila cambia, el maple de arriba cae en su lugar.
    if (apilado && apilado !== cuenta) ultima.classList.add("cae");
  }
  apilado = ultima ? ultima.textContent : "sin maples";
  // Con un maple completo, el cartel del nido invita a canjear.
  const cartel = nido.querySelector(".cartel");
  cartel.textContent = huevos >= minimo ? "¡Canjeá!" : "Canjear huevos";
  cartel.classList.toggle("llama", huevos >= minimo);
}

// Un huevo recién puesto: aparece en el pasto y, al tocarlo, vuela hasta el nido.
function huevoSuelto(nido, alJuntar) {
  // Lejos del borde izquierdo, para que no caiga sobre la pila de maples.
  const el = cosa("huevo", 7, 8, azar(36, zona.x2 + 6), azar(zona.y1 + 10, zona.y2 + 14), "button");
  el.classList.add("suelto");
  el.style.animationDelay = `${azar(0, 1)}s`;
  el.setAttribute("aria-label", "Juntar el huevo");
  el.addEventListener("click", () => {
    el.disabled = true;
    el.classList.add("volando");
    mover(el, Number(nido.style.getPropertyValue("--x")) + 5, Number(nido.style.getPropertyValue("--y")) - 4);
    setTimeout(() => { el.remove(); alJuntar(); }, 450);
  }, { once: true });
}

// --- Gallinas -------------------------------------------------------------------------------
// Cuadros de la tira: 0 quieta · 1 y 2 caminando · 3 picoteando · 4 echada · 5 dormida.

function crearGallina(datos, noche) {
  const x = azar(zona.x1, zona.x2);
  const y = azar(zona.y1, zona.y2);
  const el = cosa(`gallina-${datos.color}`, 16, 16, x, y, "button");
  el.setAttribute("aria-label", `Acariciar a ${datos.nombre}`);
  const gallina = { el, x, y, estado: "quieta", queda: azar(500, 2500), destino: null, alLlegar: null, reloj: 0 };
  if (noche) {
    cuadro(el, 5);
    el.insertAdjacentHTML("beforeend", '<span class="zzz">z z</span>');
  }
  el.addEventListener("click", () => {
    globo(el, "corazon", 7, 6);
    if (!noche) Object.assign(gallina, { estado: "quieta", queda: 900 });
  });
  return gallina;
}

function irA(gallina, x, y, velocidad, alLlegar) {
  Object.assign(gallina, { estado: "caminando", destino: { x, y }, velocidad, alLlegar });
}

function picotear(gallina, cuanto) {
  Object.assign(gallina, { estado: "picoteando", queda: cuanto });
}

function vivir(gallina, tic) {
  gallina.reloj += tic;
  if (gallina.estado === "caminando") {
    const dx = gallina.destino.x - gallina.x;
    const dy = gallina.destino.y - gallina.y;
    const falta = Math.hypot(dx, dy);
    const paso = (gallina.velocidad * tic) / 1000;
    if (falta <= paso) {
      const alLlegar = gallina.alLlegar;
      Object.assign(gallina, { estado: "quieta", queda: azar(600, 2000), alLlegar: null });
      if (alLlegar) alLlegar();
    } else {
      gallina.x += (dx / falta) * paso;
      gallina.y += (dy / falta) * paso;
      gallina.el.classList.toggle("espejo", dx < 0);
      const ritmo = gallina.velocidad > 12 ? 100 : 200;
      cuadro(gallina.el, 1 + (Math.floor(gallina.reloj / ritmo) % 2));
      mover(gallina.el, gallina.x, gallina.y);
    }
    return;
  }
  gallina.queda -= tic;
  if (gallina.estado === "picoteando") cuadro(gallina.el, Math.floor(gallina.reloj / 240) % 2 ? 3 : 0);
  else if (gallina.estado === "echada") cuadro(gallina.el, 4);
  else cuadro(gallina.el, 0);
  if (gallina.queda > 0) return;
  // Terminó lo que estaba haciendo: elige al azar qué hacer ahora.
  const dado = Math.random();
  if (dado < 0.5) irA(gallina, azar(zona.x1, zona.x2), azar(zona.y1, zona.y2), 7);
  else if (dado < 0.75) picotear(gallina, azar(1000, 2200));
  else if (dado < 0.87) Object.assign(gallina, { estado: "echada", queda: azar(3000, 6000) });
  else Object.assign(gallina, { estado: "quieta", queda: azar(800, 2500) });
}

// Cada tanto aparece un bichito y la gallina más cercana sale corriendo a comérselo.
function bichos(tic) {
  if (!gallinas.length) return;
  if (bicho) {
    cuadro(bicho.el, Math.floor(Date.now() / 200) % 2);
    return;
  }
  proximoBicho -= tic;
  if (proximoBicho > 0) return;
  const x = azar(zona.x1 + 4, zona.x2 + 8);
  const y = azar(zona.y1 + 12, zona.y2 + 12);
  bicho = { el: cosa("bichito", 6, 5, x, y) };
  const cerca = gallinas.reduce((a, b) => (Math.hypot(a.x - x, a.y - y) < Math.hypot(b.x - x, b.y - y) ? a : b));
  irA(cerca, x - 12, y - 11, 26, () => {
    picotear(cerca, 900);
    bicho.el.remove();
    bicho = null;
    proximoBicho = azar(15000, 35000);
    globo(cerca.el, "corazon", 7, 6);
  });
}

// Al tocar el comedero o el bebedero, las gallinas se acercan.
function llamar(a) {
  const x = Number(a.style.getPropertyValue("--x"));
  const y = Number(a.style.getPropertyValue("--y"));
  gallinas.forEach((gallina, i) => {
    irA(gallina, x - 14 + i * 9, y - 12 + (i % 2) * 3, 16, () => picotear(gallina, 2600));
  });
}
