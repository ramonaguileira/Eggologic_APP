// Lo que muestra cada panel. Cada función recibe el estado que mandó el servidor y devuelve HTML.
// Los botones llevan data-accion; js/app.js escucha los toques y llama al servidor.

// Lo que el cliente va eligiendo en pantalla y todavía no mandó.
export const eleccion = {
  // La tienda avanza de a un paso: rubros → cantidad → direccion → pago → listo.
  paso: "rubros", producto: null, cantidad: 1, donde: "mia", direccion: "", telefono: "", pago: null, faltan: 0,
  plan: "dos_anios", color: "blanca", medio: null, medioRecarga: null,
  // Huevos que están en la chacra esperando que los junten (lo lleva js/app.js).
  sueltos: 0,
};

const n = (numero) => Number(numero).toLocaleString("es-UY", { maximumFractionDigits: 1 });
// Para escribir texto del usuario dentro del HTML sin que se rompa.
export const limpio = (texto) =>
  String(texto ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const fecha = (iso) => new Date(iso).toLocaleDateString("es-UY", { day: "numeric", month: "long" });
const eggo = '<img class="pixel" src="arte/eggo-chico.png" width="13" height="16" alt="">';

// Cada opción es [valor, texto] o [valor, texto, apagada].
function opciones(nombre, lista, elegida) {
  return `<div class="elegir">${lista
    .map(
      ([valor, texto, apagada]) =>
        `<label class="${apagada ? "apagada" : ""}"><input type="radio" name="${nombre}" value="${valor}" ${String(valor) === String(elegida) ? "checked" : ""} ${apagada ? "disabled" : ""}><span>${texto}</span></label>`
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
  const porAnio = estado.adopcion.huevos_por_anio;
  const huevosDelPlan = { dos_anios: `${porAnio * 2} huevos garantizados`, un_anio: `${porAnio} huevos garantizados`, mensual: "entre 17 y 18 huevos por mes" };
  const lleno = estado.gallinas.length >= estado.adopcion.maximo_por_cuenta;
  let adoptar = "";
  if (lleno) adoptar = `<p>Ya tenés ${estado.adopcion.maximo_por_cuenta} gallinas, que es el máximo por cuenta.</p>`;
  else if (!estado.adopcion.lugares) adoptar = "<p>Por ahora no quedan gallinas para adoptar. Te avisamos cuando haya lugar.</p>";
  else {
    adoptar = `<form data-accion="adoptar">
      <p>Pagás por adelantado y tu gallina te va dando sus huevos: entre 17 y 18 por mes. Con 15 juntados ya los podés pedir.</p>
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
  // Los que todavía están sueltos en la chacra no cuentan hasta que se juntan.
  const hay = Math.max(estado.huevos.para_pedir - eleccion.sueltos, 0);
  if (!estado.gallinas.length && !estado.huevos.juntados_en_total) {
    return `<p>Acá se juntan los huevos de tus gallinas. Todavía no tenés ninguna.</p>
      <button class="boton ancho" data-abrir="gallinas">Adoptar una gallina</button>`;
  }
  // Un maple de 15 que se va llenando. Los completos se apilan: dos de 15 hacen uno de 30.
  const enMaple = hay % 15;
  const de30 = Math.floor(hay / 30);
  const de15 = Math.floor((hay % 30) / 15);
  const pila = [de30 ? `${de30} ${de30 === 1 ? "maple" : "maples"} de 30` : "", de15 ? "1 maple de 15" : ""].filter(Boolean).join(" y ");
  const maple = Array.from({ length: 15 }, (_, i) => `<i class="${i < enMaple ? "lleno" : ""}"></i>`).join("");
  const tamanos = [...new Set(estado.productos.map((p) => p.huevos))].sort((a, b) => a - b);
  const botones = tamanos
    .map((t) => `<button class="boton" data-accion="pedir-huevos" data-huevos="${t}" ${hay < t ? "disabled" : ""}>Canjear ${t}</button>`)
    .join("");
  const minimo = estado.huevos.minimo;
  return `<p class="fila"><span class="numero">${n(hay)}</span> <span>huevos juntados</span></p>
    <div class="maple">${maple}</div>
    ${pila ? `<p class="centro"><strong>Ya completaste ${pila}</strong></p>` : ""}
    ${eleccion.sueltos ? `<p class="destacado">Hay ${eleccion.sueltos} ${eleccion.sueltos === 1 ? "huevo recién puesto" : "huevos recién puestos"} en la chacra. Tocalos para mandarlos al maple.</p>` : ""}
    <p>${hay >= minimo ? "Ya podés canjearlos. Te los llevamos sin costo." : `Con ${minimo} ya los podés canjear. Faltan ${minimo - hay}.`}</p>
    <form data-accion="entrega">${entrega(estado)}</form>
    <div>${botones}</div>`;
}

// --- Tienda ---------------------------------------------------------------------------------

// Lo único que se vende hoy son huevos. Los demás rubros se ven apagados hasta que se liberen.
const RUBROS = [
  ["huevos", "Huevos", true], ["huerta", "Huerta"], ["carnes", "Carnes"],
  ["hierbas", "Hierbas"], ["frutas", "Frutas"], ["miel", "Miel"],
];

// El producto y la cantidad que el cliente lleva elegidos.
export function compra(estado) {
  // Solo cuentan los envases que se pueden llenar con los huevos que hay.
  const caben = estado.productos.filter((p) => p.huevos <= estado.tienda.huevos_disponibles);
  const producto = caben.find((p) => String(p.id) === String(eleccion.producto)) || caben[0];
  if (!producto) return null;
  const cantidad = Math.max(1, Math.min(eleccion.cantidad, 50, Math.floor(estado.tienda.huevos_disponibles / producto.huevos)));
  return { producto, cantidad, total: producto.precio * cantidad, totalEggos: producto.precio_eggos * cantidad };
}

// Un paso ya resuelto: queda en una línea y se puede tocar para cambiarlo.
const resuelto = (paso, texto) =>
  `<button class="resuelto" data-accion="paso" data-paso="${paso}"><span>${texto}</span><span class="chico">cambiar</span></button>`;

function tienda(estado) {
  const paso = eleccion.paso;
  if (paso === "rubros") {
    const rubros = RUBROS.map(([rubro, nombre, abierto]) =>
      abierto
        ? `<button class="rubro" data-accion="paso" data-paso="cantidad"><img class="pixel" src="arte/huevo.png" width="28" height="32" alt="">${nombre}</button>`
        : `<button class="rubro" disabled>${nombre}<span class="chico">pronto</span></button>`
    ).join("");
    return `<div class="rubros">${rubros}</div>
      ${estado.pedidos.length ? '<button class="enlace" data-abrir="pedidos">Mis pedidos</button>' : ""}`;
  }

  const c = compra(estado);
  if (!c) {
    return "<p>Por ahora no quedan huevos para encargar. Volvé a mirar en unos días.</p>";
  }
  const queCompra = `${c.cantidad} × ${limpio(c.producto.nombre)}`;

  if (paso === "cantidad") {
    const lleno = (c.cantidad + 1) * c.producto.huevos > estado.tienda.huevos_disponibles || c.cantidad >= 50;
    return `<h3>¿Cuántos huevos?</h3>
      ${opciones("producto", estado.productos.map((p) => [p.id, `<strong>${limpio(p.nombre)}</strong><br><span class="chico">${p.huevos} huevos</span>`, p.huevos > estado.tienda.huevos_disponibles]), c.producto.id)}
      <div class="cantidad grande"><button data-accion="menos" aria-label="Uno menos" ${c.cantidad <= 1 ? "disabled" : ""}>−</button><span>${c.cantidad}</span><button data-accion="mas" aria-label="Uno más" ${lleno ? "disabled" : ""}>+</button></div>
      <p class="centro tenue">${n(c.cantidad * c.producto.huevos)} huevos · $ ${n(c.total)}</p>
      <button class="boton ancho" data-accion="paso" data-paso="direccion">Elegir</button>`;
  }

  const tieneDireccion = estado.yo.direccion && estado.yo.telefono;
  if (paso === "direccion") {
    const campoDireccion = `<label class="campo">Dirección de entrega<input name="direccion" required maxlength="200" value="${limpio(eleccion.direccion)}" autocomplete="street-address"></label>`;
    const pregunta = tieneDireccion
      ? `${opciones("donde", [["mia", `<strong>En mi dirección</strong><br><span class="chico">${limpio(estado.yo.direccion)}</span>`], ["otra", "<strong>Otra dirección</strong>"]], eleccion.donde)}
         ${eleccion.donde === "otra" ? campoDireccion : ""}`
      : `${campoDireccion}
         <label class="campo">Teléfono<input name="telefono" type="tel" required maxlength="40" value="${limpio(eleccion.telefono)}" autocomplete="tel"></label>`;
    return `${resuelto("cantidad", queCompra)}
      <h3>¿Dónde te los llevamos?</h3>
      <form data-accion="direccion">${pregunta}
        <button class="boton ancho">Elegir</button>
        <p class="chico tenue centro">Entregamos en El Tesoro y La Barra.</p></form>`;
  }

  const donde = tieneDireccion && eleccion.donde === "mia" ? estado.yo.direccion : eleccion.direccion;
  if (paso === "pago") {
    const conEggos = eleccion.pago === "eggos";
    const pagos = [
      ["contra_entrega", "<strong>Efectivo</strong>"],
      ["transferencia", "<strong>Transferencia</strong>"],
      estado.tienda.mercado_pago ? ["mercado_pago", "<strong>Tarjeta</strong>"] : ["mercado_pago", '<strong>Tarjeta</strong><br><span class="chico">pronto</span>', true],
      ["eggos", `<strong>Eggos</strong><br><span class="chico">${n(estado.eggos.descuento)} % off</span>`],
    ];
    return `${resuelto("cantidad", queCompra)}${resuelto("direccion", limpio(donde))}
      <h3>¿Cómo pagás?</h3>
      <form data-accion="pedir">${opciones("pago", pagos, eleccion.pago)}
        ${eleccion.pago ? `<p class="fila"><span class="crece">Total</span><span class="numero">${conEggos ? eggo + " " + n(c.totalEggos) : "$ " + n(c.total)}</span></p>` : ""}
        <button class="boton ancho" ${eleccion.pago ? "" : "disabled"}>Encargar</button></form>`;
  }

  // Listo: el pedido recién hecho es el primero de la lista.
  const pedido = estado.pedidos[0];
  return `<div class="centro"><img class="pixel flota" src="arte/huevo.png" width="42" height="48" alt="">
      <h3>¡Pedido hecho!</h3>
      ${pedido ? `<p>${limpio(pedido.items.join(", "))}<br><strong>${llegada(pedido)}</strong></p>` : ""}
      ${pedido && pedido.forma_pago === "transferencia" ? `<p class="destacado">Transferí $ ${n(pedido.total)}.<br>${limpio(estado.tienda.datos_transferencia)}</p>` : ""}
      <button class="boton" data-abrir="pedidos">Mis pedidos</button>
      <button class="boton secundario" data-abrir="tienda">Encargar más</button></div>`;
}

function pedidos(estado) {
  const lista = estado.pedidos
    .map((p) => `<li><span>${limpio(p.items.join(", "))}<br><span class="chico tenue">${p.forma_pago_texto}</span></span><strong>${llegada(p)}</strong></li>`)
    .join("");
  return lista ? `<ul class="lista">${lista}</ul>` : `<p>Todavía no hiciste ningún pedido.</p>
    <button class="boton ancho" data-abrir="tienda" data-paso="cantidad">Quiero encargar huevos</button>`;
}

function recargar(estado) {
  const paquetes = estado.eggos.paquetes.map((p) => `<button class="boton" data-accion="recargar" data-paquete="${p}">${n(p)}</button>`).join("");
  return `${eleccion.faltan ? `<p class="destacado">Te faltan <strong>${n(eleccion.faltan)} Eggos</strong> para este pedido. Cargá y seguí.</p>` : ""}
    <p class="fila"><img class="pixel" src="arte/eggo.png" width="44" height="54" alt=""><span><span class="numero">${n(estado.eggos.saldo)}</span> Eggos</span></p>
    <p>Se cargan en paquetes: 1 Eggo = $ 1. Con Eggos todo sale ${n(estado.eggos.descuento)} % menos.</p>
    <h3>¿Cómo pagás la carga?</h3>
    ${opciones("medioRecarga", mediosDePago(estado), eleccion.medioRecarga || mediosDePago(estado)[0][0])}
    <h3>¿Cuántos Eggos?</h3>
    <div>${paquetes}</div>
    ${eleccion.faltan ? '<button class="enlace" data-abrir="tienda" data-paso="pago">Volver al pedido</button>' : ""}`;
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
      <button class="boton" data-abrir="recargar">Cargar</button></div>
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
    ${estado.pedidos.length ? '<button class="boton secundario" data-abrir="pedidos">Mis pedidos</button>' : ""}
    ${movimientos ? `<h3>Movimientos de Eggos</h3><ul class="lista">${movimientos}</ul>` : ""}
    <button class="enlace" data-accion="recorrido">Ver el recorrido de nuevo</button>
    <p class="chico tenue">${limpio(estado.yo.email)}</p>
    <button class="enlace" data-accion="salir">Salir de la cuenta</button>`;
}

export const paneles = {
  gallinas: { titulo: "Gallinas", pintar: gallinas },
  huevos: { titulo: "Canjear huevos", pintar: huevos },
  tienda: { titulo: "Tienda", pintar: tienda },
  pedidos: { titulo: "Mis pedidos", pintar: pedidos },
  recargar: { titulo: "Cargar Eggos", pintar: recargar },
  residuos: { titulo: "Residuos", pintar: residuos },
  impacto: { titulo: "Impacto", pintar: impacto },
  cuenta: { titulo: "Mi cuenta", pintar: cuenta },
};
