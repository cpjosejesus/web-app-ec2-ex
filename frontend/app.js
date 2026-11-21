// Lógica de la interfaz. No conoce URLs ni métodos HTTP: todo pasa por api.js.
import * as api from "./api.js";

const ROOM_TYPES = { single: "Simple", double: "Doble", family: "Familiar", suite: "Suite" };
const STATUS_LABELS = {
  available: "Disponible", maintenance: "Mantenimiento",
  confirmed: "Confirmada", checked_in: "Hospedado", checked_out: "Finalizada", cancelled: "Cancelada",
};

// ---------- utilidades ----------
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function money(value) {
  return Number(value).toLocaleString("es-BO", { maximumFractionDigits: 2, useGrouping: false });
}

// El estado de la API (checked_in) se convierte en modificador BEM (badge--checked-in).
function badge(status) {
  const modifier = "badge--" + String(status).replace(/_/g, "-");
  return `<span class="badge ${esc(modifier)}">${esc(STATUS_LABELS[status] || status)}</span>`;
}

function emptyRow(colspan, text) {
  return `<tr><td class="table__cell table__cell--empty" colspan="${colspan}">${text}</td></tr>`;
}

function showMessage(text, isError = false) {
  const message = document.getElementById("message");
  message.textContent = text;
  message.classList.toggle("message--error", isError);
  message.hidden = false;
  clearTimeout(showMessage.timer);
  showMessage.timer = setTimeout(() => { message.hidden = true; }, isError ? 6000 : 4000);
}

// Ejecuta una acción y, si la API devuelve error (por ejemplo un 422 de una regla
// de negocio), muestra su mensaje al recepcionista.
async function run(action) {
  try {
    await action();
  } catch (error) {
    showMessage(error.message, true);
  }
}

// ---------- pestañas ----------
const tabButtons = document.querySelectorAll("[data-tab]");
tabButtons.forEach((button) => {
  button.addEventListener("click", () => {
    tabButtons.forEach((b) => b.classList.toggle("tabs__button--active", b === button));
    document.querySelectorAll("[data-tab-panel]").forEach((panel) => {
      panel.hidden = panel.dataset.tabPanel !== button.dataset.tab;
    });
  });
});

// ---------- habitaciones ----------
async function loadRooms() {
  const rooms = await api.listRooms();
  const body = document.getElementById("rooms-body");
  body.innerHTML = rooms.length === 0
    ? emptyRow(6, "No hay habitaciones")
    : rooms.map((r) => `
      <tr>
        <td class="table__cell">${esc(r.number)}</td>
        <td class="table__cell">${esc(ROOM_TYPES[r.type] || r.type)}</td>
        <td class="table__cell">Bs ${money(r.price_per_night)}</td>
        <td class="table__cell">${esc(r.capacity)}</td>
        <td class="table__cell">${badge(r.status)}</td>
        <td class="table__cell">
          <div class="table__actions">
            <button type="button" class="button button--small button--secondary"
              data-action="toggle-maintenance" data-id="${r.id}" data-status="${esc(r.status)}">
              ${r.status === "maintenance" ? "Habilitar" : "Mantenimiento"}
            </button>
            <button type="button" class="button button--small button--danger"
              data-action="delete-room" data-id="${r.id}">Eliminar</button>
          </div>
        </td>
      </tr>`).join("");

  // También llena el select del formulario de reservas.
  document.getElementById("reservation-room").innerHTML = rooms
    .map((r) => `<option value="${r.id}">${esc(r.number)} · ${esc(ROOM_TYPES[r.type] || r.type)} · Bs ${money(r.price_per_night)}</option>`)
    .join("");
}

document.getElementById("room-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form));
  data.price_per_night = Number(data.price_per_night);
  data.capacity = Number(data.capacity);

  run(async () => {
    const room = await api.createRoom(data);
    form.reset();
    showMessage("Habitación " + room.number + " creada");
    await loadRooms();
  });
});

// ---------- huéspedes ----------
async function loadGuests() {
  const guests = await api.listGuests();
  const body = document.getElementById("guests-body");
  body.innerHTML = guests.length === 0
    ? emptyRow(4, "No hay huéspedes")
    : guests.map((g) => `
      <tr>
        <td class="table__cell">${esc(g.full_name)}</td>
        <td class="table__cell">${esc(g.email)}</td>
        <td class="table__cell">${esc(g.document)}</td>
        <td class="table__cell">
          <button type="button" class="button button--small button--danger"
            data-action="delete-guest" data-id="${g.id}">Eliminar</button>
        </td>
      </tr>`).join("");

  document.getElementById("reservation-guest").innerHTML = guests
    .map((g) => `<option value="${g.id}">${esc(g.full_name)}</option>`)
    .join("");
}

document.getElementById("guest-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form));

  run(async () => {
    const guest = await api.createGuest(data);
    form.reset();
    showMessage("Huésped " + guest.full_name + " registrado");
    await loadGuests();
  });
});

// ---------- reservas ----------
async function loadReservations() {
  const status = document.getElementById("reservation-filter").value;
  const reservations = await api.listReservations(status);
  const body = document.getElementById("reservations-body");
  body.innerHTML = reservations.length === 0
    ? emptyRow(10, "No hay reservas")
    : reservations.map((r) => `
      <tr>
        <td class="table__cell">${r.id}</td>
        <td class="table__cell">${esc(r.room_number)}</td>
        <td class="table__cell">${esc(r.guest_name)}</td>
        <td class="table__cell">${esc(r.check_in)}</td>
        <td class="table__cell">${esc(r.check_out)}</td>
        <td class="table__cell">${esc(r.nights)}</td>
        <td class="table__cell">${esc(r.guests_count)}</td>
        <td class="table__cell">${money(r.total_price)}</td>
        <td class="table__cell">${badge(r.status)}</td>
        <td class="table__cell">
          <div class="table__actions">
            <button type="button" class="button button--small button--success"
              data-action="check-in" data-id="${r.id}">Check-in</button>
            <button type="button" class="button button--small"
              data-action="check-out" data-id="${r.id}">Check-out</button>
            <button type="button" class="button button--small button--danger"
              data-action="cancel" data-id="${r.id}">Cancelar</button>
          </div>
        </td>
      </tr>`).join("");
}

document.getElementById("reservation-filter").addEventListener("change", () => run(loadReservations));

document.getElementById("reservation-form").addEventListener("submit", (event) => {
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form));
  data.room_id = Number(data.room_id);
  data.guest_id = Number(data.guest_id);
  data.guests_count = Number(data.guests_count);

  run(async () => {
    const reservation = await api.createReservation(data);
    form.reset();
    showMessage(`Reserva #${reservation.id} creada · total Bs ${money(reservation.total_price)}`);
    await loadReservations();
  });
});

// ---------- acciones de las tablas ----------
// Un solo listener por página: los botones se identifican con data-action (no con clases de estilo).
const actions = {
  "toggle-maintenance": async ({ id, status }) => {
    await api.updateRoom(id, { status: status === "maintenance" ? "available" : "maintenance" });
    await loadRooms();
  },
  "delete-room": async ({ id }) => {
    if (!confirm("¿Eliminar la habitación?")) return;
    await api.deleteRoom(id);
    showMessage("Habitación eliminada");
    await loadRooms();
  },
  "delete-guest": async ({ id }) => {
    if (!confirm("¿Eliminar el huésped?")) return;
    await api.deleteGuest(id);
    showMessage("Huésped eliminado");
    await loadGuests();
  },
  "check-in": ({ id }) => changeReservation(api.checkInReservation, id),
  "check-out": ({ id }) => changeReservation(api.checkOutReservation, id),
  "cancel": ({ id }) => changeReservation(api.cancelReservation, id),
};

async function changeReservation(apiCall, id) {
  const reservation = await apiCall(id);
  showMessage(`Reserva #${id}: ${STATUS_LABELS[reservation.status]} · total Bs ${money(reservation.total_price)}`);
  await loadReservations();
}

document.addEventListener("click", (event) => {
  const button = event.target.closest("[data-action]");
  if (!button) return;
  run(() => actions[button.dataset.action](button.dataset));
});

// ---------- inicio ----------
run(loadRooms);
run(loadGuests);
run(loadReservations);
