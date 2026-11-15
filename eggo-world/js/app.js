// Arranque de Eggo World: carga, entrada, y lo que pasa cuando se toca algo.

import { enviar, traerEstado } from "./api.js";
import { apilar, armar } from "./chacra.js";
import { compra, eleccion, paneles } from "./paneles.js";
import { recorrido, yaVioElRecorrido } from "./tour.js";

const $ = (id) => document.getElementById(id);
let estado = null;
let abierto = null;

// --- Carga: frases que van cambiando -------------------------------------------------------

const FRASES = [
  "Ubicando gallinas…", "Desenterrando larvas…", "Llenando bebederos…",
  "Preparando comederos…", "Contando huevos…", "Despertando al gallo…",
];
let frase = 0;
const cambiarFrase = setInterval(() => ($("frase").textContent = FRASES[++frase % FRASES.length]), 700);
const inicio = Date.now();

// --- Avisos cortos --------------------------------------------------------------------------

let ocultarAviso = null;
function avisar(texto, cuanto = 4000) {
  $("aviso").textContent = texto;
  $("aviso").hidden = false;
  clearTimeout(ocultarAviso);
  ocultarAviso = setTimeout(() => ($("aviso").hidden = true), cuanto);
}

// --- Pintar ---------------------------------------------------------------------------------

// --- Huevos para juntar ---------------------------------------------------------------------
// Cada huevo nuevo aparece suelto en la chacra y el cliente lo toca para mandarlo al maple.
// Cuántos lleva juntados se recuerda en el teléfono: es un juego, las cuentas las hace el servidor.
// SUPUESTO: como mucho quedan 5 por juntar; si se acumulan más, los demás se juntan solos.

const MAXIMO_DE_SUELTOS = 5;
let juntados = null;

function guardarJuntados() {
  try { localStorage.setItem(`eggo-juntados-${estado.yo.email}`, juntados); } catch { /* sin memoria, vale por esta visita */ }
}

function contarSueltos(nuevo) {
  if (juntados === null) {
    try { juntados = Number(localStorage.getItem(`eggo-juntados-${nuevo.yo.email}`) ?? NaN); } catch { juntados = NaN; }
  }
  const total = nuevo.huevos.juntados_en_total;
  const tope = Math.min(MAXIMO_DE_SUELTOS, Math.max(nuevo.huevos.para_pedir, 0));
  if (!(juntados >= total - tope && juntados <= total)) juntados = total - tope;
  return total - juntados;
}

function juntarHuevo() {
  juntados += 1;
  eleccion.sueltos -= 1;
  guardarJuntados();
  $("huevos").textContent = (estado.huevos.para_pedir - eleccion.sueltos).toLocaleString("es-UY");
  apilar(estado.huevos.para_pedir - eleccion.sueltos);
  if (abierto === "huevos") pintarPanel();
}

function pintar(nuevo) {
  const sueltos = contarSueltos(nuevo);
  const cambiaronLasGallinas = !estado || JSON.stringify(nuevo.gallinas.map((g) => [g.id, g.estado, g.color])) !== JSON.stringify(estado.gallinas.map((g) => [g.id, g.estado, g.color]));
  const cambiaronLosHuevos = !estado || nuevo.huevos.para_pedir !== estado.huevos.para_pedir || sueltos !== eleccion.sueltos || nuevo.levantes.length !== estado.levantes.length;
  estado = nuevo;
  eleccion.sueltos = sueltos;
  guardarJuntados();
  $("saldo").textContent = estado.eggos.saldo.toLocaleString("es-UY");
  $("huevos").textContent = (estado.huevos.para_pedir - sueltos).toLocaleString("es-UY");
  $("insignia").hidden = !estado.eggos.socio;
  if (cambiaronLasGallinas || cambiaronLosHuevos) armar(estado, abrir, sueltos, juntarHuevo);
  if (abierto) pintarPanel();
}

function pintarPanel() {
  const cuerpo = $("panel-cuerpo");
  const altura = cuerpo.scrollTop;
  $("panel-titulo").textContent = paneles[abierto].titulo;
  cuerpo.innerHTML = paneles[abierto].pintar(estado);
  cuerpo.scrollTop = altura;
}

// La tienda se abre en el primer paso, salvo que se pida otro (el botón "Quiero encargar huevos").
function abrir(panel, paso = "rubros") {
  abierto = panel;
  if (panel === "tienda") eleccion.paso = paso;
  if (panel !== "tienda" && panel !== "recargar") eleccion.faltan = 0;
  $("panel").hidden = $("fondo-panel").hidden = false;
  pintarPanel();
  $("panel-cuerpo").scrollTop = 0;
}

function cerrar() {
  abierto = null;
  $("panel").hidden = $("fondo-panel").hidden = true;
}

// --- Hablar con el servidor -----------------------------------------------------------------

async function hacer(camino, datos, mensaje) {
  try {
    const respuesta = await enviar(camino, datos);
    if (respuesta.estado) pintar(respuesta.estado);
    const pago = respuesta.pago;
    if (pago && pago.ir_a) {
      // Mercado Pago: se va a pagar y después vuelve solo a la chacra.
      window.location.href = pago.ir_a;
    } else if (pago && pago.transferir) {
      avisar(`Transferí $ ${pago.transferir.monto.toLocaleString("es-UY")}. ${pago.transferir.datos} Lo acreditamos cuando lo veamos.`, 12000);
    } else if (mensaje) {
      avisar(mensaje);
    }
    return respuesta;
  } catch (error) {
    if (error.sinEntrar) mostrarEntrada();
    else avisar(error.message, 6000);
    return null;
  }
}

function campos(form) {
  return Object.fromEntries(new FormData(form).entries());
}

// La dirección puede estar en el formulario de al lado (panel de huevos).
function datosDeEntrega() {
  const form = $("panel-cuerpo").querySelector('form[data-accion="entrega"]');
  return form ? campos(form) : {};
}

const ACCIONES = {
  mas: () => { eleccion.cantidad = compra(estado).cantidad + 1; pintarPanel(); },
  menos: () => { eleccion.cantidad = compra(estado).cantidad - 1; pintarPanel(); },
  paso: (el) => { eleccion.paso = el.dataset.paso; pintarPanel(); $("panel-cuerpo").scrollTop = 0; },
  recorrido: () => { cerrar(); recorrido(); },
  recargar: (el) => {
    const medio = $("panel-cuerpo").querySelector('input[name="medioRecarga"]:checked');
    hacer("recargas/", { paquete: Number(el.dataset.paquete), medio: medio && medio.value });
  },
  "pedir-huevos": (el) => hacer("huevos/pedir/", { huevos: Number(el.dataset.huevos), ...datosDeEntrega() }, "¡Canje hecho! Mirá cuándo llega en Mis pedidos."),
  "dar-larvas": (el) => hacer("larvas/dar/", { gallina: Number(el.dataset.id), cantidad: Number(el.dataset.cantidad) }, "¡Qué festín! Va a poner más huevos."),
  renombrar: (el) => {
    const nombre = window.prompt("¿Cómo se llama?", el.dataset.nombre);
    if (nombre) hacer(`gallinas/${el.dataset.id}/nombre/`, { nombre });
  },
  salir: async () => { await hacer("salir/"); window.location.reload(); },
};

const FORMULARIOS = {
  adoptar: async (datos) => {
    const respuesta = await hacer("gallinas/adoptar/", datos);
    if (respuesta && !respuesta.pago) { cerrar(); avisar(`¡${datos.nombre} ya está en tu chacra!`); }
  },
  direccion: (datos) => {
    if (datos.direccion) eleccion.direccion = datos.direccion.trim();
    if (datos.telefono) eleccion.telefono = datos.telefono.trim();
    eleccion.paso = "pago";
    pintarPanel();
  },
  pedir: async () => {
    const c = compra(estado);
    const pedido = { items: [{ producto: c.producto.id, cantidad: c.cantidad }], forma_pago: eleccion.pago };
    // Con "otra dirección", o si todavía no había ninguna guardada, va la que se escribió recién.
    if (eleccion.donde === "otra" || !estado.yo.direccion || !estado.yo.telefono) {
      pedido.direccion = eleccion.direccion;
      pedido.telefono = eleccion.telefono || estado.yo.telefono;
    }
    const respuesta = await hacer("pedidos/", pedido);
    if (!respuesta) return;
    Object.assign(eleccion, { paso: "listo", cantidad: 1, donde: "mia", direccion: "", pago: null, faltan: 0 });
    if (abierto) pintarPanel();
  },
  levante: (datos) => hacer("levantes/", datos, "¡Listo! Pasamos a buscar tu balde."),
  perfil: (datos) => hacer("perfil/", datos, "Datos guardados."),
  entrega: () => {},
};

document.addEventListener("click", (evento) => {
  const abre = evento.target.closest("[data-abrir]");
  if (abre) return abrir(abre.dataset.abrir, abre.dataset.paso);
  const accion = evento.target.closest("button[data-accion]");
  if (accion && ACCIONES[accion.dataset.accion]) ACCIONES[accion.dataset.accion](accion);
});
document.addEventListener("submit", (evento) => {
  const form = evento.target.closest("form[data-accion]");
  if (!form) return;
  evento.preventDefault();
  FORMULARIOS[form.dataset.accion](campos(form));
});
// Al elegir una opción (plan, color, forma de pago) se recuerda y se actualiza el panel.
document.addEventListener("change", (evento) => {
  if (evento.target.type !== "radio" || !(evento.target.name in eleccion)) return;
  eleccion[evento.target.name] = evento.target.value;
  // Pagar con Eggos sin tener suficientes lleva derecho a cargarlos.
  if (evento.target.name === "pago" && evento.target.value === "eggos") {
    const faltan = compra(estado).totalEggos - estado.eggos.saldo;
    if (faltan > 0) {
      Object.assign(eleccion, { pago: null, faltan });
      return abrir("recargar");
    }
  }
  const nombre = $("panel-cuerpo").querySelector('input[name="nombre"]');
  const escrito = nombre && nombre.value;
  pintarPanel();
  const otraVez = $("panel-cuerpo").querySelector('form[data-accion="adoptar"] input[name="nombre"]');
  if (otraVez && escrito) otraVez.value = escrito;
});
$("cerrar").addEventListener("click", cerrar);
$("fondo-panel").addEventListener("click", cerrar);
document.addEventListener("keydown", (evento) => evento.key === "Escape" && cerrar());

let ajustar = null;
window.addEventListener("resize", () => {
  clearTimeout(ajustar);
  ajustar = setTimeout(() => estado && armar(estado, abrir, eleccion.sueltos, juntarHuevo), 200);
});

// --- Entrar ---------------------------------------------------------------------------------

function mostrar(id) {
  clearInterval(cambiarFrase);
  for (const otra of ["carga", "entrada", "chacra"]) $(otra).hidden = otra !== id;
}

function mostrarEntrada() {
  cerrar();
  mostrar("entrada");
  // El botón de Google se arma solo (ver los data-* en el HTML): acá solo mostramos el aviso
  // si no hay identificador de Google cargado, y el error si Google nos devolvió uno.
  const cliente = document.querySelector('meta[name="google-client-id"]').content;
  $("sin-google").hidden = !!cliente;
  const parametros = new URLSearchParams(location.search);
  if (parametros.get("error")) {
    avisar(parametros.get("error"), 8000);
    history.replaceState(null, "", location.pathname);
  }
}

async function arrancar() {
  try {
    const nuevo = await traerEstado();
    // La pantalla de carga se ve al menos un momento, para que se lean las frases.
    await new Promise((seguir) => setTimeout(seguir, Math.max(0, 1500 - (Date.now() - inicio))));
    mostrar("chacra");
    pintar(nuevo);
    // La primera vez, un recorrido corto por los botones.
    if (!yaVioElRecorrido()) recorrido();
  } catch (error) {
    if (error.sinEntrar) mostrarEntrada();
    else { mostrar("entrada"); avisar(error.message, 8000); }
  }
}

arrancar();
// Los pedidos y las larvas cambian solos con el tiempo: se refresca cada tanto, sin molestar.
setInterval(async () => {
  if (estado && document.visibilityState === "visible") {
    try { pintar(await traerEstado()); } catch { /* si falla, se prueba en la próxima vuelta */ }
  }
}, 60000);
