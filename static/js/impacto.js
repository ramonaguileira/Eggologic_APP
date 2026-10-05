// Detalles de "Mi impacto": el número principal cuenta hasta su valor y la calculadora
// responde al deslizador. Sin JavaScript la página muestra los mismos números, quietos.
(function () {
  function formatear(valor, decimales) {
    return new Intl.NumberFormat("es-UY", {
      minimumFractionDigits: decimales,
      maximumFractionDigits: decimales,
    }).format(valor);
  }

  var sinAnimaciones = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  document.querySelectorAll("[data-contar]").forEach(function (elemento) {
    var final = parseFloat(elemento.dataset.contar);
    var decimales = parseInt(elemento.dataset.decimales || "0", 10);
    if (sinAnimaciones || !final) {
      return;
    }
    var duracion = 1200;
    var inicio = null;
    function paso(momento) {
      if (inicio === null) {
        inicio = momento;
      }
      var avance = Math.min((momento - inicio) / duracion, 1);
      var suavizado = 1 - Math.pow(1 - avance, 3);
      elemento.textContent = formatear(final * suavizado, decimales);
      if (avance < 1) {
        requestAnimationFrame(paso);
      }
    }
    requestAnimationFrame(paso);
  });

  var calculadora = document.getElementById("calculadora");
  if (calculadora) {
    var deslizador = calculadora.querySelector("input[type=range]");
    var docenas = document.getElementById("calc-docenas");
    var kilos = document.getElementById("calc-kg");
    var kgPorHuevo = parseFloat(calculadora.dataset.kgPorHuevo);
    var calcular = function () {
      var porMes = parseInt(deslizador.value, 10);
      docenas.textContent = porMes;
      kilos.textContent = formatear(porMes * 12 * 12 * kgPorHuevo, 0);
    };
    deslizador.addEventListener("input", calcular);
    calcular();
  }
})();
