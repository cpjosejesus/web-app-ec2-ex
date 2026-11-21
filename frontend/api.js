// Cliente del backend: todas las llamadas HTTP a la API pasan por aquí.
// app.js solo usa estas funciones y no hace fetch directamente.

// URL del backend: mismo host desde donde se abrió la página, puerto 8000.
// Funciona igual en localhost y en la IP pública de la EC2.
const API_URL = `${location.protocol}//${location.hostname}:8000/api`;

// Hace la petición y devuelve el JSON de la respuesta (o null si no hay cuerpo, p. ej. 204).
// Si la API responde con error (400, 404, 409, 422…), lanza un Error con el mensaje
// de { "error": "..." } para mostrárselo al recepcionista.
async function request(path, { method = "GET", data } = {}) {
  const options = { method, headers: {} };
  if (data !== undefined) {
    options.headers["Content-Type"] = "application/json";
    options.body = JSON.stringify(data);
  }

  let res;
  try {
    res = await fetch(API_URL + path, options);
  } catch (networkError) {
    throw new Error("No se pudo conectar con el servidor");
  }

  const text = await res.text();
  const body = text ? JSON.parse(text) : null;
  if (!res.ok) {
    throw new Error((body && body.error) || `Error ${res.status}`);
  }
  return body;
}

const api = {
  // habitaciones
  listRooms: () => request("/rooms"),
  createRoom: (data) => request("/rooms", { method: "POST", data }),
  updateRoom: (id, data) => request(`/rooms/${id}`, { method: "PUT", data }),
  deleteRoom: (id) => request(`/rooms/${id}`, { method: "DELETE" }),

  // huéspedes
  listGuests: () => request("/guests"),
  createGuest: (data) => request("/guests", { method: "POST", data }),
  deleteGuest: (id) => request(`/guests/${id}`, { method: "DELETE" }),

  // reservas
  listReservations: (status) => request("/reservations" + (status ? `?status=${encodeURIComponent(status)}` : "")),
  createReservation: (data) => request("/reservations", { method: "POST", data }),
  cancelReservation: (id) => request(`/reservations/${id}/cancel`, { method: "PATCH" }),
  checkInReservation: (id) => request(`/reservations/${id}/check-in`, { method: "PATCH" }),
  checkOutReservation: (id) => request(`/reservations/${id}/check-out`, { method: "PATCH" }),
};
