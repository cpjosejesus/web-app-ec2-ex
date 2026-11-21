// Única capa que conoce la URL, los métodos HTTP y el formato de transporte.
// El mismo host permite usar localhost o la IP pública de la EC2.
const HotelApi = (() => {
  const baseUrl = `${location.protocol}//${location.hostname}:8000/api`;

  async function request(path, { method = "GET", data } = {}) {
    let response;
    try {
      response = await fetch(baseUrl + path, {
        method,
        headers: {
          Accept: "application/json",
          ...(data === undefined ? {} : { "Content-Type": "application/json" }),
        },
        ...(data === undefined ? {} : { body: JSON.stringify(data) }),
      });
    } catch {
      throw new Error("No se pudo conectar con el servidor");
    }

    if (response.status === 204) return null;

    let body;
    try {
      body = await response.json();
    } catch {
      throw new Error(response.ok
        ? "El servidor devolvió una respuesta inválida"
        : `No se pudo completar la operación (código ${response.status})`);
    }
    if (!response.ok) {
      throw new Error(body?.error || `No se pudo completar la operación (código ${response.status})`);
    }
    return body;
  }

  function queryString(filters = {}) {
    const query = new URLSearchParams();
    for (const [key, value] of Object.entries(filters)) {
      if (value !== undefined && value !== null && value !== "") query.set(key, value);
    }
    return query.size ? `?${query}` : "";
  }

  return Object.freeze({
    listRooms: (status) => request("/rooms" + queryString({ status })),
    getRoom: (id) => request(`/rooms/${id}`),
    createRoom: (data) => request("/rooms", { method: "POST", data }),
    updateRoom: (id, data) => request(`/rooms/${id}`, { method: "PUT", data }),
    deleteRoom: (id) => request(`/rooms/${id}`, { method: "DELETE" }),
    listGuests: () => request("/guests"),
    getGuest: (id) => request(`/guests/${id}`),
    createGuest: (data) => request("/guests", { method: "POST", data }),
    deleteGuest: (id) => request(`/guests/${id}`, { method: "DELETE" }),
    listReservations: (filters) => request("/reservations" + queryString(filters)),
    getReservation: (id) => request(`/reservations/${id}`),
    createReservation: (data) => request("/reservations", { method: "POST", data }),
    cancelReservation: (id) => request(`/reservations/${id}/cancel`, { method: "PATCH" }),
    checkInReservation: (id) => request(`/reservations/${id}/check-in`, { method: "PATCH" }),
    checkOutReservation: (id) => request(`/reservations/${id}/check-out`, { method: "PATCH" }),
  });
})();
