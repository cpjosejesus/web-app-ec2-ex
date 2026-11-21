from datetime import date, datetime
from zoneinfo import ZoneInfo

from ..repositories import reservations as reservation_repository
from . import guests as guest_service, rooms as room_service
from .errors import BusinessRuleError, NotFoundError, ValidationError


def list_reservations(status=None, guest_id=None):
    return reservation_repository.list_reservations(status, guest_id)


def get_reservation(reservation_id):
    reservation = reservation_repository.get_reservation(reservation_id)
    if reservation is None:
        raise NotFoundError("Reserva no encontrada")
    return reservation


def create_reservation(data):
    required = ("room_id", "guest_id", "check_in", "check_out", "guests_count")
    missing = [field for field in required if data.get(field) in (None, "")]
    if missing:
        raise ValidationError(f"Faltan campos: {', '.join(missing)}")

    room = room_service.get_room(_parse_id(data["room_id"], "room_id"))
    guest = guest_service.get_guest(_parse_id(data["guest_id"], "guest_id"))

    try:
        check_in = date.fromisoformat(data["check_in"])
        check_out = date.fromisoformat(data["check_out"])
    except (TypeError, ValueError, OverflowError) as error:
        raise ValidationError("Fechas en formato AAAA-MM-DD") from error

    if check_out <= check_in:
        raise BusinessRuleError("La fecha de salida debe ser posterior a la fecha de ingreso")

    today = datetime.now(ZoneInfo("America/La_Paz")).date()
    if check_in < today:
        raise BusinessRuleError("La fecha de ingreso no puede ser anterior a hoy")

    capacity_error = f"La cantidad de personas debe ser un entero entre 1 y la capacidad de la habitación ({room.capacity})"
    try:
        guests_count = int(data["guests_count"])
    except (TypeError, ValueError, OverflowError) as error:
        raise BusinessRuleError(capacity_error) from error

    if isinstance(data["guests_count"], bool):
        raise BusinessRuleError(capacity_error)
    if isinstance(data["guests_count"], float) and data["guests_count"] != guests_count:
        raise BusinessRuleError(capacity_error)
    if guests_count < 1 or guests_count > room.capacity:
        raise BusinessRuleError(capacity_error)

    if room.status != "available":
        raise BusinessRuleError("La habitación está en mantenimiento y no se puede reservar")

    existing = reservation_repository.find_overlapping_reservation(
        room.id, check_in, check_out, ("confirmed", "checked_in")
    )
    if existing is not None:
        raise BusinessRuleError("La habitación ya tiene una reserva para las fechas seleccionadas")

    nights = (check_out - check_in).days
    total_price = nights * room.price_per_night

    reservation = reservation_repository.create_reservation(
        room=room,
        guest=guest,
        check_in=check_in,
        check_out=check_out,
        guests_count=guests_count,
        status="confirmed",
        total_price=total_price,
    )
    return reservation


def cancel_reservation(reservation_id):
    reservation = get_reservation(reservation_id)
    reservation.status = "cancelled"
    return reservation_repository.save_reservation(reservation)


def check_in_reservation(reservation_id):
    reservation = get_reservation(reservation_id)
    reservation.status = "checked_in"
    return reservation_repository.save_reservation(reservation)


def check_out_reservation(reservation_id):
    reservation = get_reservation(reservation_id)
    reservation.status = "checked_out"
    return reservation_repository.save_reservation(reservation)


def _parse_id(value, field):
    try:
        return int(value)
    except (TypeError, ValueError, OverflowError) as error:
        raise ValidationError(f"{field} debe ser numérico") from error
