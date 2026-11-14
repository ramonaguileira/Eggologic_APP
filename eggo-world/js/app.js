// Arranque de Eggo World: carga, entrada, y lo que pasa cuando se toca algo.

import { enviar, traerEstado } from "./api.js";
import { armar } from "./chacra.js";
import { eleccion, limpio, paneles } from "./paneles.js";

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

function pintar(nuevo) {
  const cambiaronLasGallinas = !estado || JSON.stringify(nuevo.gallinas.map((g) => [g.id, g.estado, g.color])) !== JSON.stringify(estado.gallinas.map((g) => [g.id, g.estado, g.color]));
  const cambiaronLosHuevos = !estado || nuevo.huevos.para_pedir !== estado.huevos.para_pedir || nuevo.levantes.length !== estado.levantes.length;
  estado = nuevo;
  $("saldo").textContent = estado.eggos.saldo.toLocaleString("es-UY");
  $("huevos").textContent = estado.huevos.para_pedir.toLocaleString("es-UY");
  $("insignia").hidden = !estado.eggos.socio;
  if (cambiaronLasGallinas || cambiaronLosHuevos) armar(estado, abrir);
  if (abierto) pintarPanel();
}

function pintarPanel() {
  const cuerpo = $("panel-cuerpo");
  const altura = cuerpo.scrollTop;
  $("panel-titulo").textContent = paneles[abierto].titulo;
  cuerpo.innerHTML = paneles[abierto].pintar(estado);
  cuerpo.scrollTop = altura;
}

function abrir(panel) {
  abierto = panel;
  if (panel === "tienda" && !eleccion.pago) eleccion.pago = estado.eggos.saldo > 0 ? "eggos" : estado.tienda.mercado_pago ? "mercado_pago" : "contra_entrega";
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
  mas: (el) => { eleccion.carrito[el.dataset.id] = Math.min((eleccion.carrito[el.dataset.id] || 0) + 1, 50); pintarPanel(); },
  menos: (el) => { eleccion.carrito[el.dataset.id] = Math.max((eleccion.carrito[el.dataset.id] || 0) - 1, 0); pintarPanel(); },
  recargar: (el) => {
    const medio = $("panel-cuerpo").querySelector('input[name="medioRecarga"]:checked');
    hacer("recargas/", { paquete: Number(el.dataset.paquete), medio: medio && medio.value });
  },
  "pedir-huevos": (el) => hacer("huevos/pedir/", { huevos: Number(el.dataset.huevos), ...datosDeEntrega() }, "¡Pedido hecho! Mirá cuándo llega en la Tienda."),
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
  pedir: async (datos) => {
    const items = Object.entries(eleccion.carrito).map(([producto, cantidad]) => ({ producto: Number(producto), cantidad }));
    const respuesta = await hacer("pedidos/", { ...datos, items, forma_pago: datos.pago }, "¡Pedido hecho! Abajo ves cuándo llega.");
    if (respuesta) eleccion.carrito = {};
    if (respuesta && abierto) pintarPanel();
  },
  levante: (datos) => hacer("levantes/", datos, "¡Listo! Pasamos a buscar tu balde."),
  perfil: (datos) => hacer("perfil/", datos, "Datos guardados."),
  entrega: () => {},
};

document.addEventListener("click", (evento) => {
  const abre = evento.target.closest("[data-abrir]");
  if (abre) return abrir(abre.dataset.abrir);
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
  ajustar = setTimeout(() => estado && armar(estado, abrir), 200);
});

// --- Entrar ---------------------------------------------------------------------------------

function mostrar(id) {
  clearInterval(cambiarFrase);
  for (const otra of ["carga", "entrada", "chacra"]) $(otra).hidden = otra !== id;
}

function mostrarEntrada() {
  cerrar();
  mostrar("entrada");
  const cliente = document.querySelector('meta[name="google-client-id"]').content;
  const listo = () => window.google && window.google.accounts;
  let intentos = 0;
  const esperar = setInterval(() => {
    if (!cliente || intentos++ > 40) {
      clearInterval(esperar);
      $("sin-google").hidden = false;
    } else if (listo()) {
      clearInterval(esperar);
      window.google.accounts.id.initialize({
        client_id: cliente,
        callback: async (respuesta) => {
          mostrar("carga");
          if (await hacer("entrar/google/", { credential: respuesta.credential })) arrancar();
          else mostrar("entrada");
        },
      });
      window.google.accounts.id.renderButton($("boton-google"), { theme: "filled_blue", size: "large", text: "continue_with", locale: "es" });
    }
  }, 150);
}

async function arrancar() {
  try {
    const nuevo = await traerEstado();
    // La pantalla de carga se ve al menos un momento, para que se lean las frases.
    await new Promise((seguir) => setTimeout(seguir, Math.max(0, 1500 - (Date.now() - inicio))));
    mostrar("chacra");
    pintar(nuevo);
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
