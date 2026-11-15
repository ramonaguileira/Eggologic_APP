// El único archivo que habla con el servidor.

function galleta(nombre) {
  const par = document.cookie.split("; ").find((trozo) => trozo.startsWith(nombre + "="));
  return par ? decodeURIComponent(par.split("=")[1]) : "";
}

async function pedir(metodo, camino, datos) {
  const respuesta = await fetch(`/api/v1/${camino}`, {
    method: metodo,
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", "X-CSRFToken": galleta("csrftoken") },
    body: datos ? JSON.stringify(datos) : undefined,
  });
  let cuerpo = {};
  try {
    cuerpo = await respuesta.json();
  } catch {
    // Una respuesta sin JSON (por ejemplo, un error del servidor) se trata como error.
  }
  if (!respuesta.ok) {
    const error = new Error(cuerpo.error || "Algo salió mal. Probá de nuevo en un rato.");
    error.sinEntrar = respuesta.status === 401;
    throw error;
  }
  return cuerpo;
}

export const traerEstado = () => pedir("GET", "estado/");
export const enviar = (camino, datos = {}) => pedir("POST", camino, datos);
