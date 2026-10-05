// Botones + y − de la tienda, total en vivo y cuánto residuo ayuda a rescatar el pedido.
// Sin JavaScript la tienda funciona igual: se escriben las cantidades a mano.
(function () {
  var productos = document.querySelectorAll(".producto");
  var total = document.getElementById("total");
  var rescate = document.getElementById("rescate");
  var pesos = new Intl.NumberFormat("es-UY", { maximumFractionDigits: 0 });
  var kilos = new Intl.NumberFormat("es-UY", { maximumFractionDigits: 1 });

  function cantidad(campo) {
    var numero = parseInt(campo.value, 10);
    return isNaN(numero) || numero < 0 ? 0 : numero;
  }

  function actualizar() {
    var importe = 0;
    var huevos = 0;
    productos.forEach(function (producto) {
      var unidades = cantidad(producto.querySelector("input"));
      importe += unidades * parseFloat(producto.dataset.precio);
      huevos += unidades * parseInt(producto.dataset.huevos, 10);
      producto.classList.toggle("elegido", unidades > 0);
    });
    total.textContent = "$ " + pesos.format(importe);
    if (rescate) {
      rescate.textContent = huevos === 0
        ? "Elegí tus huevos y te mostramos cuántos residuos ayudás a rescatar."
        : "🥚 " + huevos + " huevos que ayudan a rescatar unos " +
          kilos.format(huevos * parseFloat(rescate.dataset.kgPorHuevo)) + " kg de residuos de restaurantes.";
    }
  }

  productos.forEach(function (producto) {
    var campo = producto.querySelector("input");
    producto.querySelector(".menos").addEventListener("click", function () {
      campo.value = Math.max(0, cantidad(campo) - 1);
      actualizar();
    });
    producto.querySelector(".mas").addEventListener("click", function () {
      campo.value = Math.min(parseInt(campo.max, 10), cantidad(campo) + 1);
      actualizar();
    });
    campo.addEventListener("input", actualizar);
  });

  actualizar();
})();
