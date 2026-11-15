// El recorrido de la primera vez: muestra dónde está cada botón y para qué sirve.
// Cada paso es [qué resaltar, título, texto]. Sin nada que resaltar, el cartel va al medio.

const PASOS = [
  [null, "¡Bienvenido a tu chacra!", "Te muestro dónde está cada cosa. Es un minuto."],
  ["#encargar", "Quiero encargar huevos", "El camino más corto: elegís cuántos huevos querés y te los llevamos a tu casa. Son huevos de verdad."],
  ['[data-tour="tienda"]', "Tienda", "Acá comprás. Hoy hay huevos; de a poco se suman huerta, miel y más."],
  ['[data-tour="gallinas"]', "Gallinas", "Adoptá una gallina, ponele nombre y te va dando sus huevos."],
  ['[data-tour="huevos"]', "Canjear huevos", "Los huevos de tus gallinas se juntan en el maple. Con 15 los canjeás y te los llevamos."],
  ['[data-tour="residuos"]', "Residuos", "Pedí que retiremos tus restos de cocina. Se convierten en larvas para tus gallinas."],
  ['[data-tour="impacto"]', "Impacto", "Lo que lograste: huevos recibidos, residuos transformados y tu nivel."],
  ['[data-tour="cuenta"]', "Mi cuenta", "Tus datos, tus pedidos y tus movimientos."],
  ['[data-abrir="cuenta"].contador', "Tus Eggos", "Tu saldo para usar en Eggologic. Pagando con Eggos todo sale menos."],
];

const CLAVE = "eggo-recorrido-visto";

export function yaVioElRecorrido() {
  // Si el teléfono no deja recordar, no se le muestra en cada visita.
  try { return localStorage.getItem(CLAVE) === "si"; } catch { return true; }
}

export function recorrido() {
  const app = document.getElementById("app");
  if (document.getElementById("tour")) return;
  const tour = document.createElement("div");
  tour.id = "tour";
  tour.innerHTML = `<div class="foco"></div>
    <div class="burbuja" role="dialog" aria-live="polite"><h3></h3><p></p>
      <div class="fila"><button class="enlace" data-tour-salir>Saltar</button><button class="boton" data-tour-seguir></button></div></div>`;
  app.append(tour);
  const foco = tour.querySelector(".foco");
  const burbuja = tour.querySelector(".burbuja");
  let paso = 0;

  function terminar() {
    try { localStorage.setItem(CLAVE, "si"); } catch { /* se verá de nuevo la próxima vez */ }
    tour.remove();
  }

  function mostrar() {
    const [selector, titulo, texto] = PASOS[paso];
    const destino = selector && document.querySelector(selector);
    burbuja.querySelector("h3").textContent = titulo;
    burbuja.querySelector("p").textContent = texto;
    burbuja.querySelector("[data-tour-seguir]").textContent = paso === PASOS.length - 1 ? "¡Listo!" : "Siguiente";
    const marco = app.getBoundingClientRect();
    if (!destino) {
      Object.assign(foco.style, { left: "50%", top: "40%", width: "0", height: "0" });
      Object.assign(burbuja.style, { top: "40%", bottom: "auto" });
      return;
    }
    // El recuadro abarca el dibujo y su cartelito.
    const caja = destino.getBoundingClientRect();
    const cartel = (destino.querySelector(".cartel") || destino).getBoundingClientRect();
    const izquierda = Math.min(caja.left, cartel.left) - marco.left;
    const derecha = Math.max(caja.right, cartel.right) - marco.left;
    const abajo = cartel.bottom - marco.top;
    const arriba = caja.top - marco.top;
    Object.assign(foco.style, {
      left: `${izquierda - 6}px`, top: `${arriba - 6}px`,
      width: `${derecha - izquierda + 12}px`, height: `${abajo - arriba + 12}px`,
    });
    // El cartel va del lado donde hay más lugar.
    if (arriba > marco.height / 2) Object.assign(burbuja.style, { top: "auto", bottom: `${marco.height - arriba + 18}px` });
    else Object.assign(burbuja.style, { top: `${abajo + 18}px`, bottom: "auto" });
  }

  tour.addEventListener("click", (evento) => {
    // Los toques no llegan a la chacra mientras dura el recorrido.
    evento.stopPropagation();
    if (evento.target.closest("[data-tour-salir]")) return terminar();
    if (!evento.target.closest("[data-tour-seguir]")) return;
    paso += 1;
    if (paso >= PASOS.length) terminar();
    else mostrar();
  });
  mostrar();
}
