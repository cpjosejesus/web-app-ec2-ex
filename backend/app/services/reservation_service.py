from datetime import date

from ..repositories.guest_repositories import get_guest as repo_get_guest
from ..repositories.reservation_repositories import (
    cancel_reservation as repo_cancel_reservation,
    check_in_reservation as repo_check_in_reservation,
    check_out_reservation as repo_check_out_reservation,
    create_reservation as repo_create_reservation,
    get_reservation as repo_get_reservation,
    list_reservations as repo_list_reservations,
)
from ..repositories.room_repositories import get_room as repo_get_room

RESERVATION_STATUSES = ("Confirmada", "Hospedado", "Finalizada", "Cancelada")


def list_reservations(status=None, guest_id=None):
    return repo_list_reservations(status=status, guest_id=guest_id)


def get_reservation(reservation_id):
    reservation = repo_get_reservation(reservation_id)
    if reservation is None:
        return {"error": "Reserva no encontrada", "status": 404}
    return reservation


def create_reservation(data):
    data = data or {}
    missing = [f for f in ("room_id", "guest_id", "check_in", "check_out", "guests_count") if data.get(f) in (None, "")]
    if missing:
        return {"error": f"Faltan campos: {', '.join(missing)}", "status": 400}

    try:
        room_id = int(data["room_id"])
        guest_id = int(data["guest_id"])
        guests_count = int(data["guests_count"])
        check_in = date.fromisoformat(str(data["check_in"]))
        check_out = date.fromisoformat(str(data["check_out"]))
    except (TypeError, ValueError):
        return {"error": "Fechas en formato AAAA-MM-DD y campos numéricos válidos", "status": 400}

    room = repo_get_room(room_id)
    if room is None:
        return {"error": "Habitación no encontrada", "status": 404}

    guest = repo_get_guest(guest_id)
    if guest is None:
        return {"error": "Huésped no encontrado", "status": 404}

    if check_in < date.today():
        return {"error": "No se puede registrar una reserva en una fecha pasada", "status": 422} #Regla 1

    if check_out <= check_in:
        return {"error": "La fecha de salida debe ser posterior a la fecha de ingreso", "status": 422} #Regla 2

    if room.status == "Mantenimiento":
        return {"error": "La habitación está en mantenimiento y no puede reservarse", "status": 422} #Regla 3

    if guests_count <= 0:
        return {"error": "La cantidad de huéspedes debe ser al menos 1", "status": 422}
    if guests_count > room.capacity:
        return {
            "error": f"La cantidad de huéspedes ({guests_count}) supera la capacidad de la habitación ({room.capacity})",
            "status": 422, #Regla 4
        }

    nights = (check_out - check_in).days
    total_price = nights * room.price_per_night

    return repo_create_reservation(
        room=room,
        guest=guest,
        check_in=check_in,
        check_out=check_out,
        guests_count=guests_count,
        total_price=total_price,
        status="Confirmada",
    )


def cancel_reservation(reservation_id):
    reservation = repo_get_reservation(reservation_id)
    if reservation is None:
        return {"error": "Reserva no encontrada", "status": 404}
    if reservation.status == "Cancelada":
        return {"error": "No se puede modificar una reserva cancelada", "status": 422} #Regla 5
    return repo_cancel_reservation(reservation)


def check_in_reservation(reservation_id):
    reservation = repo_get_reservation(reservation_id)
    if reservation is None:
        return {"error": "Reserva no encontrada", "status": 404}
    if reservation.status == "Cancelada":
        return {"error": "No se puede modificar una reserva cancelada", "status": 422}
    return repo_check_in_reservation(reservation)


def check_out_reservation(reservation_id):
    reservation = repo_get_reservation(reservation_id)
    if reservation is None:
        return {"error": "Reserva no encontrada", "status": 404}
    if reservation.status == "Cancelada":
        return {"error": "No se puede modificar una reserva cancelada", "status": 422}
    return repo_check_out_reservation(reservation)