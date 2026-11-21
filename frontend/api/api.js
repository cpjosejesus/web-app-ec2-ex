const API = `${location.protocol}//${location.hostname}:8000/api`;

async function handleResponse(response, fallbackError) {
  let data = null;

  if (response.status !== 204) {
    const rawText = await response.text();
    if (rawText) {
      data = JSON.parse(rawText);
    }
  }

  if (!response.ok) {
    if (data && data.error) {
      throw new Error(data.error);
    }
    throw new Error(`${fallbackError}: HTTP ${response.status}`);
  }

  return data;
}

// ---------- habitaciones ----------
export async function loadRooms_api() {
  const response = await fetch(`${API}/rooms`);
  return await handleResponse(response, "Error al cargar habitaciones");
}

export async function Room_api(id) {
  const response = await fetch(`${API}/rooms/${id}`);
  return await handleResponse(response, "Error al cargar habitación específica");
}

export async function createRoom_api(data) {
  const response = await fetch(`${API}/rooms`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return await handleResponse(response, "Error al crear habitación");
}

export async function updateRoom_api(id, data) {
  const response = await fetch(`${API}/rooms/${id}`, {
    method: "PUT",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return await handleResponse(response, "Error al actualizar habitación");
}

export async function deleteRoom_api(id) {
  const response = await fetch(`${API}/rooms/${id}`, { method: "DELETE" });
  return await handleResponse(response, "Error al eliminar habitación");
}

// ---------- huéspedes ----------
export async function Guests_api() {
  const response = await fetch(`${API}/guests`);
  return await handleResponse(response, "Error al cargar huéspedes");
}

export async function SpecificGuest_api(id) {
  const response = await fetch(`${API}/guests/${id}`);
  return await handleResponse(response, "Error al cargar huésped específico");
}

export async function createGuest_api(data) {
  const response = await fetch(`${API}/guests`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return await handleResponse(response, "Error al registrar huésped");
}

export async function deleteGuest_api(id) {
  const response = await fetch(`${API}/guests/${id}`, { method: "DELETE" });
  return await handleResponse(response, "Error al eliminar huésped");
}

// ---------- reservas ----------
export async function Reservations_api(status = "") {
  const query = status ? `?status=${encodeURIComponent(status)}` : "";
  const response = await fetch(`${API}/reservations${query}`);
  return await handleResponse(response, "Error al cargar reservas");
}

export async function SpecificReservation_api(id) {
  const response = await fetch(`${API}/reservations/${id}`);
  return await handleResponse(response, "Error al cargar reserva específica");
}

export async function createReservation_api(data) {
  const response = await fetch(`${API}/reservations`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(data),
  });
  return await handleResponse(response, "Error al crear reserva");
}

export async function changeReservation_api(id, action) {
  const response = await fetch(`${API}/reservations/${id}/${action}`, { method: "PATCH" });
  return await handleResponse(response, "Error al cambiar estado de reserva");
}