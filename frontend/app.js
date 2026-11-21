// Interfaz de la recepción. Las llamadas al backend están en api.js (objeto `api`).

const ROOM_TYPES = { single: "Simple", double: "Doble", family: "Familiar", suite: "Suite" };
const STATUS_LABELS = {
  available: "Disponible", maintenance: "Mantenimiento",
  confirmed: "Confirmada", checked_in: "Hospedado", checked_out: "Finalizada", cancelled: "Cancelada",
};

// ---------- utilidades ----------
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

function showMessage(text, isError) {
  const msg = document.getElementById("msg");
  msg.textContent = text;
  msg.className = isError ? "message message--error" : "message";
  msg.hidden = false;
  clearTimeout(showMessage.timer);
  showMessage.timer = setTimeout(() => { msg.hidden = true; }, 4000);
}

// Modificador BEM del badge: "checked_in" -> "badge--checked-in"
function badgeModifier(status) {
  return "badge--" + String(status).replace(/_/g, "-");
}

// ---------- pestañas ----------
document.querySelectorAll(".tabs__button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tabs__button").forEach((b) => b.classList.remove("tabs__button--active"));
    button.classList.add("tabs__button--active");
    document.querySelectorAll("[data-tab-panel]").forEach((tab) => { tab.hidden = true; });
    document.getElementById("tab-" + button.dataset.tab).hidden = false;
  });
});

// ---------- habitaciones ----------
async function loadRooms() {
  try {
    const rooms = await api.listRooms();
    const body = document.getElementById("rooms-body");
    if (rooms.length === 0) {
      body.innerHTML = '<tr><td colspan="6" class="table__cell table__cell--empty">No hay habitaciones</td></tr>';
    } else {
      body.innerHTML = rooms.map((r) => `
        <tr>
          <td class="table__cell">${esc(r.number)}</td>
          <td class="table__cell">${esc(ROOM_TYPES[r.type] || r.type)}</td>
          <td class="table__cell">Bs ${esc(r.price_per_night)}</td>
          <td class="table__cell">${esc(r.capacity)}</td>
          <td class="table__cell"><span class="badge ${badgeModifier(r.status)}">${esc(STATUS_LABELS[r.status])}</span></td>
          <td class="table__cell">
            <button class="button button--small button--muted" onclick="toggleMaintenance(${r.id}, '${esc(r.status)}')">
              ${r.status === "maintenance" ? "Habilitar" : "Mantenimiento"}
            </button>
            <button class="button button--small button--danger" onclick="deleteRoom(${r.id})">Eliminar</button>
          </td>
        </tr>`).join("");
    }
    // también llena el select del formulario de reservas
    document.getElementById("reservation-room").innerHTML = rooms
      .map((r) => `<option value="${r.id}">${esc(r.number)} · ${esc(ROOM_TYPES[r.type])} · Bs ${esc(r.price_per_night)}</option>`)
      .join("");
  } catch (error) {
    showMessage(error.message, true);
  }
}

document.getElementById("room-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form));
  data.price_per_night = Number(data.price_per_night);
  data.capacity = Number(data.capacity);

  try {
    const room = await api.createRoom(data);
    form.reset();
    showMessage("Habitación " + room.number + " creada");
    loadRooms();
  } catch (error) {
    showMessage(error.message, true);
  }
});

async function toggleMaintenance(id, status) {
  try {
    await api.updateRoom(id, { status: status === "maintenance" ? "available" : "maintenance" });
    loadRooms();
  } catch (error) {
    showMessage(error.message, true);
  }
}

async function deleteRoom(id) {
  if (!confirm("¿Eliminar la habitación?")) return;
  try {
    await api.deleteRoom(id);
    showMessage("Habitación eliminada");
    loadRooms();
  } catch (error) {
    showMessage(error.message, true);
  }
}

// ---------- huéspedes ----------
async function loadGuests() {
  try {
    const guests = await api.listGuests();
    const body = document.getElementById("guests-body");
    if (guests.length === 0) {
      body.innerHTML = '<tr><td colspan="4" class="table__cell table__cell--empty">No hay huéspedes</td></tr>';
    } else {
      body.innerHTML = guests.map((g) => `
        <tr>
          <td class="table__cell">${esc(g.full_name)}</td>
          <td class="table__cell">${esc(g.email)}</td>
          <td class="table__cell">${esc(g.document)}</td>
          <td class="table__cell"><button class="button button--small button--danger" onclick="deleteGuest(${g.id})">Eliminar</button></td>
        </tr>`).join("");
    }
    document.getElementById("reservation-guest").innerHTML = guests
      .map((g) => `<option value="${g.id}">${esc(g.full_name)}</option>`)
      .join("");
  } catch (error) {
    showMessage(error.message, true);
  }
}

document.getElementById("guest-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form));

  try {
    const guest = await api.createGuest(data);
    form.reset();
    showMessage("Huésped " + guest.full_name + " registrado");
    loadGuests();
  } catch (error) {
    showMessage(error.message, true);
  }
});

async function deleteGuest(id) {
  if (!confirm("¿Eliminar el huésped?")) return;
  try {
    await api.deleteGuest(id);
    showMessage("Huésped eliminado");
    loadGuests();
  } catch (error) {
    showMessage(error.message, true);
  }
}

// ---------- reservas ----------
async function loadReservations() {
  try {
    const status = document.getElementById("reservation-filter").value;
    const reservations = await api.listReservations(status);
    const body = document.getElementById("reservations-body");
    if (reservations.length === 0) {
      body.innerHTML = '<tr><td colspan="10" class="table__cell table__cell--empty">No hay reservas</td></tr>';
      return;
    }
    body.innerHTML = reservations.map((r) => `
      <tr>
        <td class="table__cell">${r.id}</td>
        <td class="table__cell">${esc(r.room_number)}</td>
        <td class="table__cell">${esc(r.guest_name)}</td>
        <td class="table__cell">${esc(r.check_in)}</td>
        <td class="table__cell">${esc(r.check_out)}</td>
        <td class="table__cell">${esc(r.nights)}</td>
        <td class="table__cell">${esc(r.guests_count)}</td>
        <td class="table__cell">${esc(r.total_price)}</td>
        <td class="table__cell"><span class="badge ${badgeModifier(r.status)}">${esc(STATUS_LABELS[r.status])}</span></td>
        <td class="table__cell">
          <button class="button button--small button--success" onclick="changeReservation(${r.id}, 'check-in')">Check-in</button>
          <button class="button button--small" onclick="changeReservation(${r.id}, 'check-out')">Check-out</button>
          <button class="button button--small button--danger" onclick="changeReservation(${r.id}, 'cancel')">Cancelar</button>
        </td>
      </tr>`).join("");
  } catch (error) {
    showMessage(error.message, true);
  }
}

document.getElementById("reservation-filter").addEventListener("change", loadReservations);

document.getElementById("reservation-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const form = event.target;
  const data = Object.fromEntries(new FormData(form));
  data.room_id = Number(data.room_id);
  data.guest_id = Number(data.guest_id);
  data.guests_count = Number(data.guests_count);

  try {
    const reservation = await api.createReservation(data);
    form.reset();
    showMessage("Reserva #" + reservation.id + " creada · total Bs " + reservation.total_price);
    loadReservations();
  } catch (error) {
    showMessage(error.message, true);
  }
});

const RESERVATION_ACTIONS = {
  "check-in": api.checkInReservation,
  "check-out": api.checkOutReservation,
  cancel: api.cancelReservation,
};

async function changeReservation(id, action) {
  try {
    const reservation = await RESERVATION_ACTIONS[action](id);
    showMessage("Reserva #" + id + ": " + STATUS_LABELS[reservation.status]);
    loadReservations();
  } catch (error) {
    showMessage(error.message, true);
  }
}

// ---------- inicio ----------
loadRooms();
loadGuests();
loadReservations();
