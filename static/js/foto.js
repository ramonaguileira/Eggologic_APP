// Achica la foto del retiro en el celular antes de mandarla: una foto de 5 a 10 MB queda en
// unos 300 KB. Sube más rápido con poca señal y la base no se llena (las fotos se guardan ahí).
// Si algo falla, se manda la foto original.
(function () {
  var LADO_MAXIMO = 1600; // SUPUESTO: alcanza para ver bien los bultos.
  var CALIDAD = 0.8;
  var campo = document.getElementById("id_foto");
  if (!campo || !window.DataTransfer || !window.createImageBitmap) return;

  campo.addEventListener("change", function () {
    var original = campo.files[0];
    if (!original) return;
    createImageBitmap(original)
      .then(function (imagen) {
        var escala = Math.min(1, LADO_MAXIMO / Math.max(imagen.width, imagen.height));
        var lienzo = document.createElement("canvas");
        lienzo.width = Math.round(imagen.width * escala);
        lienzo.height = Math.round(imagen.height * escala);
        lienzo.getContext("2d").drawImage(imagen, 0, 0, lienzo.width, lienzo.height);
        lienzo.toBlob(
          function (blob) {
            if (!blob || blob.size >= original.size) return;
            var nombre = original.name.replace(/\.[^.]*$/, "") + ".jpg";
            var archivos = new DataTransfer();
            archivos.items.add(new File([blob], nombre, { type: "image/jpeg" }));
            campo.files = archivos.files;
          },
          "image/jpeg",
          CALIDAD
        );
      })
      .catch(function () {});
  });
})();
