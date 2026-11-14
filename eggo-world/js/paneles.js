// Lo que muestra cada panel. Cada función recibe el estado que mandó el servidor y devuelve HTML.
// Los botones llevan data-accion; js/app.js escucha los toques y llama al servidor.

// Lo que el cliente va eligiendo en pantalla y todavía no mandó.
export const eleccion = { carrito: {}, pago: null, plan: "dos_anios", color: "blanca", medio: null, medioRecarga: null };

const n = (numero) => Number(numero).toLocaleString("es-UY", { maximumFractionDigits: 1 });
// Para escribir texto del usuario dentro del HTML sin que se rompa.
export const limpio = (texto) =>
  String(texto ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const fecha = (iso) => new Date(iso).toLocaleDateString("es-UY", { day: "numeric", month: "long" });
const eggo = '<img class="pixel" src="arte/eggo-chico.png" width="13" height="16" alt="">';

function opciones(nombre, lista, elegida) {
  return `<div class="elegir">${lista
    .map(
      ([valor, texto]) =>
        `<label><input type="radio" name="${nombre}" value="${valor}" ${valor === elegida ? "checked" : ""}><span>${texto}</span></label>`
    )
    .join("")}</div>`;
}

// La dirección y el teléfono se piden recién en el primer pedido.
function entrega(estado) {
  if (estado.yo.direccion && estado.yo.telefono) {
    return `<p class="tenue chico">Entrega en ${limpio(estado.yo.direccion)}. Se cambia en Mi cuenta.</p>`;
  }
  return `<label class="campo">Dirección de entrega<input name="direccion" value="${limpio(estado.yo.direccion)}" autocomplete="street-address"></label>
    <label class="campo">Teléfono<input name="telefono" type="tel" value="${limpio(estado.yo.telefono)}" autocomplete="tel"></label>`;
}

function mediosDePago(estado) {
  const medios = [["transferencia", "Transferencia"]];
  if (estado.tienda.mercado_pago) medios.unshift(["mercado_pago", "Tarjeta (Mercado Pago)"]);
  return medios;
}

// Cuándo llega un pedido: cuenta regresiva, o el día y la hora si falta más de un día.
function llegada(pedido) {
  if (pedido.estado === "entregado") return "Entregado";
  if (pedido.estado === "cancelado") return "Cancelado";
  if (!pedido.entrega_estimada) return pedido.estado_texto;
  const cuando = new Date(pedido.entrega_estimada);
  const minutos = Math.round((cuando - Date.now()) / 60000);
  if (minutos <= 0) return "Llega en cualquier momento";
  if (minutos < 60) return `Llega en ${minutos} min`;
  if (minutos < 24 * 60) return `Llega en ${Math.floor(minutos / 60)} h ${minutos % 60} min`;
  const dia = cuando.toLocaleDateString("es-UY", { weekday: "long", day: "numeric", month: "numeric" });
  const hora = cuando.toLocaleTimeString("es-UY", { hour: "2-digit", minute: "2-digit", hour12: false });
  return `Llega el ${dia} a las ${hora}`;
}

// --- Gallinas -------------------------------------------------------------------------------

function gallinas(estado) {
  const mias = estado.gallinas
    .map((g) => {
      const detalle =
        g.estado === "pendiente"
          ? "<p>Esperando el pago. Apenas lo veamos, llega a tu chacra.</p>"
          : `<p><span class="numero">${n(g.huevos_puestos)}</span> huevos puestos</p>
             <p class="chico">Produce ${g.produccion_anual} huevos por año${g.lugar_para_larvas ? "; con larvas llega a " + (estado.adopcion.huevos_por_anio + estado.adopcion.bono_maximo) : ""}.</p>
             <p class="chico tenue">${g.en_pausa ? "En pausa: cargá Eggos para que siga poniendo." : `Plan ${g.plan_texto.toLowerCase()}, pago hasta el ${fecha(g.pago_hasta)}.`}</p>`;
      return `<div class="tarjeta fila">
          <div class="retrato" style="background-image:url('arte/gallina-${g.color}.png')"></div>
          <div class="crece"><strong>${limpio(g.nombre)}</strong>
            <button class="enlace chico" data-accion="renombrar" data-id="${g.id}" data-nombre="${limpio(g.nombre)}">cambiar nombre</button>
            ${detalle}</div></div>`;
    })
    .join("");

  const plan = estado.planes.find((p) => p.plan === eleccion.plan);
  const falta = Math.max(plan.precio - estado.eggos.saldo, 0);
  const huevosDelPlan = { dos_anios: "400 huevos garantizados", un_anio: "200 huevos garantizados", mensual: "unos 17 huevos por mes" };
  const lleno = estado.gallinas.length >= estado.adopcion.maximo_por_cuenta;
  let adoptar = "";
  if (lleno) adoptar = `<p>Ya tenés ${estado.adopcion.maximo_por_cuenta} gallinas, que es el máximo por cuenta.</p>`;
  else if (!estado.adopcion.lugares) adoptar = "<p>Por ahora no quedan gallinas para adoptar. Te avisamos cuando haya lugar.</p>";
  else {
    adoptar = `<form data-accion="adoptar">
      <p>Pagás por adelantado y tu gallina te va dando sus huevos: unos 4 por semana. Con 15 juntados ya los podés pedir.</p>
      ${opciones("plan", estado.planes.map((p) => [p.plan, `<strong>${p.nombre}</strong><br>${n(p.precio)} Eggos${p.plan === "mensual" ? " por mes" : ""}`]), eleccion.plan)}
      <p class="chico tenue">${huevosDelPlan[plan.plan]}.${plan.plan === "mensual" ? " Se cobra de tu saldo cada 30 días; la cortás cuando quieras." : ""}</p>
      <label class="campo">Nombre de tu gallina<input name="nombre" maxlength="30" required placeholder="Clota"></label>
      ${opciones("color", [["blanca", "Blanca"], ["colorada", "Colorada"], ["negra", "Negra"]], eleccion.color)}
      ${
        falta
          ? `<div class="destacado">Tenés ${n(estado.eggos.saldo)} Eggos. Te faltan <strong>$ ${n(falta)}</strong>, que pagás ahora:</div>
             ${opciones("medio", mediosDePago(estado), eleccion.medio || mediosDePago(estado)[0][0])}`
          : `<p class="destacado">Se paga con tus Eggos: te quedan ${n(estado.eggos.saldo - plan.precio)}.</p>`
      }
      <button class="boton ancho">Adoptar</button></form>`;
  }
  return `${mias ? "<h3>Mis gallinas</h3>" + mias : ""}
    <h3>Adoptar una gallina</h3>${adoptar}
    <h3>Cómo están</h3><p>${limpio(estado.granja.sanidad)}</p>`;
}

// --- Huevos ---------------------------------------------------------------------------------

function huevos(estado) {
  const hay = estado.huevos.para_pedir;
  if (!estado.gallinas.length) {
    return `<p>Acá se juntan los huevos de tus gallinas. Todavía no tenés ninguna.</p>
      <button class="boton ancho" data-abrir="gallinas">Adoptar una gallina</button>`;
  }
  const casilleros = hay > 15 ? 30 : 15;
  const maple = Array.from({ length: casilleros }, (_, i) => `<i class="${i < hay ? "lleno" : ""}"></i>`).join("");
  const tamanos = [...new Set(estado.productos.map((p) => p.huevos))].sort((a, b) => a - b);
  const botones = tamanos
    .map((t) => `<button class="boton" data-accion="pedir-huevos" data-huevos="${t}" ${hay < t ? "disabled" : ""}>Pedir ${t}</button>`)
    .join("");
  return `<p class="fila"><span class="numero">${n(hay)}</span> <span>huevos juntados</span></p>
    <div class="maple ${casilleros === 30 ? "grande" : ""}">${maple}</div>
    <p>${hay >= estado.huevos.minimo ? "Ya podés pedirlos. Te los llevamos sin costo." : `Con ${estado.huevos.minimo} ya los podés pedir. Faltan ${estado.huevos.minimo - hay}.`}</p>
    <form data-accion="entrega">${entrega(estado)}</form>
    <div>${botones}</div>`;
}

// --- Tienda ---------------------------------------------------------------------------------

function tienda(estado) {
  const conEggos = eleccion.pago === "eggos";
  let total = 0;
  const productos = estado.productos
    .map((p) => {
      const cantidad = eleccion.carrito[p.id] || 0;
      total += cantidad * (conEggos ? p.precio_eggos : p.precio);
      return `<div class="tarjeta fila">
        <div class="crece"><strong>${limpio(p.nombre)}</strong><br><span class="chico tenue">${limpio(p.descripcion) || p.huevos + " huevos"}</span><br>
          <span class="precio">$ ${n(p.precio)}</span> o <span class="precio-eggos">${eggo}${n(p.precio_eggos)}</span></div>
        <div class="cantidad"><button data-accion="menos" data-id="${p.id}" aria-label="Uno menos">−</button><span>${cantidad}</span><button data-accion="mas" data-id="${p.id}" aria-label="Uno más">+</button></div>
      </div>`;
    })
    .join("");
  const pagos = [["eggos", `Eggos<br><span class="chico">tenés ${n(estado.eggos.saldo)}</span>`]];
  if (estado.tienda.mercado_pago) pagos.push(["mercado_pago", "Tarjeta"]);
  pagos.push(["transferencia", "Transferencia"], ["contra_entrega", "Al recibir"]);
  const pedidos = estado.pedidos
    .map((p) => `<li><span>${limpio(p.items.join(", "))}<br><span class="chico tenue">${p.forma_pago_texto}</span></span><strong>${llegada(p)}</strong></li>`)
    .join("");
  const paquetes = estado.eggos.paquetes.map((p) => `<button class="boton" data-accion="recargar" data-paquete="${p}">${n(p)}</button>`).join("");
  return `<p class="destacado">Con Eggos pagás <strong>${n(estado.eggos.descuento)} % menos</strong>${estado.eggos.socio ? ", por ser socio" : ""}. Con plata te vuelve el ${n(estado.eggos.vuelta)} % en Eggos.</p>
    ${productos || "<p>Todavía no hay productos cargados.</p>"}
    <form data-accion="pedir">
      <h3>Cómo pagás</h3>${opciones("pago", pagos, eleccion.pago)}
      ${entrega(estado)}
      <p class="fila"><span class="crece">Total</span><span class="numero">${conEggos ? eggo + " " : "$ "}${n(total)}</span></p>
      <button class="boton ancho" ${total ? "" : "disabled"}>Pedir</button>
      <p class="chico tenue">Hay ${n(estado.tienda.huevos_disponibles)} huevos disponibles. Entregamos en El Tesoro y La Barra.</p>
    </form>
    <h3>Recargar Eggos</h3>
    <p>Se cargan en paquetes: 1 Eggo = $ 1.</p>
    ${opciones("medioRecarga", mediosDePago(estado), eleccion.medioRecarga || mediosDePago(estado)[0][0])}
    <div>${paquetes}</div>
    ${pedidos ? `<h3>Mis pedidos</h3><ul class="lista">${pedidos}</ul>` : ""}`;
}

// --- Residuos y larvas ----------------------------------------------------------------------

function residuos(estado) {
  const ultimo = estado.levantes[0];
  const orden = ["pedido", "retirado", "procesando", "larvas"];
  const nombres = { pedido: "Pedido", retirado: "Retirado", procesando: "Procesando", larvas: "Larvas listas" };
  let seguimiento = "";
  if (ultimo && orden.includes(ultimo.paso)) {
    const hasta = orden.indexOf(ultimo.paso);
    seguimiento = `<h3>Tu último levante</h3>
      <ul class="pasos">${orden.map((paso, i) => `<li class="${i <= hasta ? "hecho" : ""}">${nombres[paso]}</li>`).join("")}</ul>
      <p class="chico tenue">${
        ultimo.kg === null
          ? "Pasamos a buscar el balde y lo pesamos."
          : `Pesó ${n(ultimo.kg)} kg: son ${ultimo.raciones} raciones de larvas${ultimo.paso === "larvas" ? "." : ", listas el " + fecha(ultimo.larvas_listas_el) + "."}`
      }</p>`;
  }
  const activas = estado.gallinas.filter((g) => g.estado === "activa");
  let larvas = "";
  if (estado.larvas > 0) {
    const botones = activas
      .filter((g) => g.lugar_para_larvas > 0)
      .map((g) => `<button class="boton" data-accion="dar-larvas" data-id="${g.id}" data-cantidad="${Math.min(estado.larvas, g.lugar_para_larvas)}">Dárselas a ${limpio(g.nombre)}</button>`)
      .join("");
    larvas = `<div class="destacado"><p class="fila"><img class="pixel" src="arte/larva.png" width="48" height="18" alt=""> <strong>Tenés ${n(estado.larvas)} raciones de larvas.</strong></p>
      <p>${activas.length ? "Cada ración es un huevo más. Si no se las das, en unos días se las comen solas." : "Quedan guardadas para cuando adoptes una gallina."}</p>${botones}</div>`;
  }
  const yaPedido = ultimo && ultimo.paso === "pedido";
  return `${larvas}
    <p>Juntá tus restos de cocina en un balde. Lo pasamos a buscar, lo pesamos y lo convertimos en larvas para tus gallinas.</p>
    <p><strong>Cada kilo le saca un huevo más a tu gallina</strong>, hasta ${estado.adopcion.bono_maximo} por año.</p>
    ${seguimiento}
    <form data-accion="levante">
      ${yaPedido ? "" : entrega(estado) + '<label class="campo">Algo que tengamos que saber<input name="nota" maxlength="200" placeholder="Timbre, horario…"></label>'}
      <button class="boton ancho" ${yaPedido ? "disabled" : ""}>${yaPedido ? "Ya tenés un levante pedido" : `Pedir levante · ${estado.precio_del_levante} Eggos`}</button>
    </form>`;
}

// --- Impacto --------------------------------------------------------------------------------

function impacto(estado) {
  const i = estado.impacto;
  const cifra = (valor, texto) => `<div class="tarjeta"><div class="numero">${valor}</div><span class="chico">${texto}</span></div>`;
  const nivel = i.nivel;
  return `<div class="cifras">
      ${cifra(n(i.huevos_recibidos), "huevos recibidos")}
      ${cifra(n(i.kg_residuos_entregados) + " kg", "de residuos que entregaste")}
      ${cifra(n(i.huevos_extra_por_larvas), "huevos extra gracias a tus larvas")}
      ${i.kg_detras_de_mis_huevos === null ? "" : cifra(n(i.kg_detras_de_mis_huevos) + " kg", "de residuo transformado detrás de tus huevos")}
    </div>
    <h3>Tu nivel: ${limpio(nivel.nombre)}</h3>
    <div class="barra"><i style="width:${nivel.progreso}%"></i></div>
    <p class="chico tenue">${nivel.siguiente ? `Te faltan ${n(nivel.faltan)} huevos para ser ${limpio(nivel.siguiente)}.` : "Llegaste al nivel más alto."}</p>
    <h3>Entre todos</h3>
    <div class="cifras">
      ${cifra(n(i.comunidad.kg_rescatados) + " kg", "de residuos de restaurantes transformados")}
      ${cifra(n(i.comunidad.kg_larvas) + " kg", "de larvas producidas")}
      ${cifra(n(i.comunidad.huevos), "huevos puestos en la granja")}
      ${cifra(n(i.comunidad.restaurantes), "restaurantes que separan sus residuos")}
    </div>
    <p class="chico tenue">Las gallinas comen larvas criadas con afrechillo y con residuos orgánicos. Estos números salen de lo que se pesa y se registra en Eggologic.</p>`;
}

// --- Mi cuenta ------------------------------------------------------------------------------

function cuenta(estado) {
  const e = estado.eggos;
  const movimientos = e.movimientos
    .map((m) => `<li><span>${limpio(m.motivo)}${m.detalle ? "<br><span class='chico tenue'>" + limpio(m.detalle) + "</span>" : ""}</span><span class="${m.cantidad > 0 ? "mas" : "menos"}">${m.cantidad > 0 ? "+" : ""}${n(m.cantidad)}</span></li>`)
    .join("");
  const pendientes = e.recargas_pendientes
    .map((r) => `<li><span>$ ${n(r.monto)} por ${limpio(r.medio).toLowerCase()}</span><span class="tenue">esperando el pago</span></li>`)
    .join("");
  return `<div class="tarjeta fila"><img class="pixel" src="arte/eggo.png" width="44" height="54" alt="">
      <div class="crece"><div class="numero">${n(e.saldo)}</div>Eggos</div>
      <button class="boton" data-abrir="tienda">Recargar</button></div>
    <div class="tarjeta fila"><img class="pixel" src="arte/insignia.png" width="33" height="36" alt="" style="${e.socio ? "" : "filter:grayscale(1);opacity:.5"}">
      <div class="crece">${
        e.socio
          ? `<strong>Sos socio este mes.</strong><br><span class="chico">${n(e.descuento_socio)} % menos con Eggos, prioridad cuando faltan huevos y precio congelado.</span>`
          : `<strong>Insignia de socio</strong><br><span class="chico">Pasá un mes entero con ${n(e.saldo_para_ser_socio)} Eggos o más y al mes siguiente pagás ${n(e.descuento_socio)} % menos, con prioridad cuando faltan huevos.</span>`
      }</div></div>
    ${pendientes ? `<h3>Pagos pendientes</h3><ul class="lista">${pendientes}</ul><p class="chico tenue">${limpio(estado.tienda.datos_transferencia)}</p>` : ""}
    <h3>Mis datos</h3>
    <form data-accion="perfil">
      <label class="campo">Nombre<input name="nombre" value="${limpio(estado.yo.nombre)}" autocomplete="given-name"></label>
      <label class="campo">Dirección de entrega<input name="direccion" value="${limpio(estado.yo.direccion)}" autocomplete="street-address"></label>
      <label class="campo">Teléfono<input name="telefono" type="tel" value="${limpio(estado.yo.telefono)}" autocomplete="tel"></label>
      <button class="boton secundario">Guardar</button>
    </form>
    ${movimientos ? `<h3>Movimientos de Eggos</h3><ul class="lista">${movimientos}</ul>` : ""}
    <p class="chico tenue">${limpio(estado.yo.email)}</p>
    <button class="enlace" data-accion="salir">Salir de la cuenta</button>`;
}

export const paneles = {
  gallinas: { titulo: "Gallinas", pintar: gallinas },
  huevos: { titulo: "Huevos", pintar: huevos },
  tienda: { titulo: "Tienda", pintar: tienda },
  residuos: { titulo: "Residuos", pintar: residuos },
  impacto: { titulo: "Impacto", pintar: impacto },
  cuenta: { titulo: "Mi cuenta", pintar: cuenta },
};
