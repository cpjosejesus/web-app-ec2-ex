// Capa de API: es el único archivo que usa fetch.
// Centraliza la URL base, los headers y el manejo de errores.
// El resto del código llama a estas funciones y no conoce URLs ni métodos HTTP.

// Mismo host desde el que se abrió la página, puerto 8000.
// Funciona igual en localhost y en la IP pública de la EC2.
const BASE_URL = `${location.protocol}//${location.hostname}:8000/api`;

const JSON_HEADERS = { "Content-Type": "application/json" };

async function request(path, { method = "GET", body } = {}) {
  let res;
  try {
    res = await fetch(BASE_URL + path, {
      method,
      headers: body === undefined ? undefined : JSON_HEADERS,
      body: body === undefined ? undefined : JSON.stringify(body),
    });
  } catch {
    throw new Error("No se pudo conectar con el servidor");
  }

  // 204 No Content (por ejemplo al eliminar): no hay cuerpo que leer.
  const data = res.status === 204 ? null : await res.json();

  if (!res.ok) {
    throw new Error(data?.error || `Error ${res.status}`);
  }
  return data;
}

function query(params) {
  const search = new URLSearchParams();
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") search.set(key, value);
  });
  const text = search.toString();
  return text ? "?" + text : "";
}

// ---------- habitaciones ----------
export const listRooms = (status) => request("/rooms" + query({ status }));
export const createRoom = (data) => request("/rooms", { method: "POST", body: data });
export const updateRoom = (id, data) => request(`/rooms/${id}`, { method: "PUT", body: data });
export const deleteRoom = (id) => request(`/rooms/${id}`, { method: "DELETE" });

// ---------- huéspedes ----------
export const listGuests = () => request("/guests");
export const createGuest = (data) => request("/guests", { method: "POST", body: data });
export const deleteGuest = (id) => request(`/guests/${id}`, { method: "DELETE" });

// ---------- reservas ----------
export const listReservations = (status) => request("/reservations" + query({ status }));
export const createReservation = (data) => request("/reservations", { method: "POST", body: data });
export const cancelReservation = (id) => request(`/reservations/${id}/cancel`, { method: "PATCH" });
export const checkInReservation = (id) => request(`/reservations/${id}/check-in`, { method: "PATCH" });
export const checkOutReservation = (id) => request(`/reservations/${id}/check-out`, { method: "PATCH" });
