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

// ---------- pestañas ----------
document.querySelectorAll(".tabs__button").forEach((button) => {
  button.addEventListener("click", () => {
    document.querySelectorAll(".tabs__button").forEach((b) => b.classList.remove("tabs__button--active"));
    button.classList.add("tabs__button--active");
    document.querySelectorAll(".tabs__panel").forEach((tab) => { tab.hidden = true; });
    document.getElementById("tab-" + button.dataset.tab).hidden = false;
  });
});

// ---------- habitaciones ----------
async function loadRooms() {
  try {
    const rooms = await HotelApi.listRooms();
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
          <td class="table__cell"><span class="badge badge--${esc(r.status.replaceAll("_", "-"))}">${esc(STATUS_LABELS[r.status])}</span></td>
          <td class="table__cell">
            <button class="button table__action button--small button--muted" onclick="toggleMaintenance(${r.id}, '${esc(r.status)}')">
              ${r.status === "maintenance" ? "Habilitar" : "Mantenimiento"}
            </button>
            <button class="button table__action button--small button--danger" onclick="deleteRoom(${r.id})">Eliminar</button>
          </td>
        </tr>`).join("");
    }
    // también llena el select del formulario de reservas
    document.getElementById("reservation-room").innerHTML = rooms
      .filter((r) => r.status === "available")
      .map((r) => `<option value="${r.id}">${esc(r.number)} · ${esc(ROOM_TYPES[r.type])} · Bs ${esc(r.price_per_night)}</option>`)
      .join("");
  } catch (error) {
    showMessage(error.message, true);
  }
}

document.getElementById("room-form").addEventListener("submit", async (event) => {
  try {
    event.preventDefault();
    const form = event.target;
    const data = Object.fromEntries(new FormData(form));
    data.price_per_night = Number(data.price_per_night);
    data.capacity = Number(data.capacity);

    const body = await HotelApi.createRoom(data);
    form.reset();
    showMessage("Habitación " + body.number + " creada");
    loadRooms();
  } catch (error) {
    showMessage(error.message, true);
  }
});

async function toggleMaintenance(id, status) {
  try {
    await HotelApi.updateRoom(id, {
      status: status === "maintenance" ? "available" : "maintenance",
    });
    loadRooms();
  } catch (error) {
    showMessage(error.message, true);
  }
}

async function deleteRoom(id) {
  try {
    if (!confirm("¿Eliminar la habitación?")) return;
    await HotelApi.deleteRoom(id);
    showMessage("Habitación eliminada");
    loadRooms();
  } catch (error) {
    showMessage(error.message, true);
  }
}

// ---------- huéspedes ----------
async function loadGuests() {
  try {
    const guests = await HotelApi.listGuests();
    const body = document.getElementById("guests-body");
    if (guests.length === 0) {
      body.innerHTML = '<tr><td colspan="4" class="table__cell table__cell--empty">No hay huéspedes</td></tr>';
    } else {
      body.innerHTML = guests.map((g) => `
        <tr>
          <td class="table__cell">${esc(g.full_name)}</td>
          <td class="table__cell">${esc(g.email)}</td>
          <td class="table__cell">${esc(g.document)}</td>
          <td class="table__cell"><button class="button table__action button--small button--danger" onclick="deleteGuest(${g.id})">Eliminar</button></td>
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
  try {
    event.preventDefault();
    const form = event.target;
    const data = Object.fromEntries(new FormData(form));

    const body = await HotelApi.createGuest(data);
    form.reset();
    showMessage("Huésped " + body.full_name + " registrado");
    loadGuests();
  } catch (error) {
    showMessage(error.message, true);
  }
});

async function deleteGuest(id) {
  try {
    if (!confirm("¿Eliminar el huésped?")) return;
    await HotelApi.deleteGuest(id);
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
    const reservations = await HotelApi.listReservations({ status });
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
        <td class="table__cell"><span class="badge badge--${esc(r.status.replaceAll("_", "-"))}">${esc(STATUS_LABELS[r.status])}</span></td>
        <td class="table__cell">
          <button class="button table__action button--small button--success" onclick="changeReservation(${r.id}, 'checkIn')">Check-in</button>
          <button class="button table__action button--small" onclick="changeReservation(${r.id}, 'checkOut')">Check-out</button>
          <button class="button table__action button--small button--danger" onclick="changeReservation(${r.id}, 'cancel')">Cancelar</button>
        </td>
      </tr>`).join("");
  } catch (error) {
    showMessage(error.message, true);
  }
}

document.getElementById("reservation-filter").addEventListener("change", loadReservations);

document.getElementById("reservation-form").addEventListener("submit", async (event) => {
  try {
    event.preventDefault();
    const form = event.target;
    const data = Object.fromEntries(new FormData(form));
    data.room_id = Number(data.room_id);
    data.guest_id = Number(data.guest_id);
    data.guests_count = Number(data.guests_count);

    const body = await HotelApi.createReservation(data);
    form.reset();
    showMessage("Reserva #" + body.id + " creada · total Bs " + body.total_price);
    loadReservations();
  } catch (error) {
    showMessage(error.message, true);
  }
});

async function changeReservation(id, action) {
  try {
    const operations = {
      checkIn: HotelApi.checkInReservation,
      checkOut: HotelApi.checkOutReservation,
      cancel: HotelApi.cancelReservation,
    };
    const body = await operations[action](id);
    showMessage("Reserva #" + id + ": " + STATUS_LABELS[body.status]);
    loadReservations();
  } catch (error) {
    showMessage(error.message, true);
  }
}

// ---------- inicio ----------
loadRooms();
loadGuests();
loadReservations();
