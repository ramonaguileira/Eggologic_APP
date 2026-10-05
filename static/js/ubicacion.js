// Completa la ubicación del retiro con el GPS del celular, sin que el chofer tenga que hacer nada.
// Si el celular no la da (sin permiso o sin señal), el retiro se guarda igual, sin ubicación.
// Ojo: los navegadores solo comparten la ubicación en páginas https (o en localhost).
(function () {
  var estado = document.getElementById("estado-ubicacion");
  var latitud = document.getElementById("id_latitud");
  var longitud = document.getElementById("id_longitud");
  var precision = document.getElementById("id_precision_m");

  if (!navigator.geolocation) {
    estado.textContent = "Este celular no comparte la ubicación. El retiro se guarda igual.";
    return;
  }

  estado.textContent = "Tomando la ubicación…";
  navigator.geolocation.getCurrentPosition(
    function (posicion) {
      latitud.value = posicion.coords.latitude.toFixed(6);
      longitud.value = posicion.coords.longitude.toFixed(6);
      precision.value = Math.round(posicion.coords.accuracy);
      estado.textContent = "📍 Ubicación registrada (± " + precision.value + " m).";
    },
    function () {
      estado.textContent = "No se pudo tomar la ubicación. El retiro se guarda igual, sin ubicación.";
    },
    { enableHighAccuracy: true, timeout: 15000 }
  );
})();
