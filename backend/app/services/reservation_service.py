from datetime import date, datetime, time, timedelta

from ..repository.guest_repository import GuestRepository
from ..repository.reservation_repository import ReservationRepository
from ..repository.room_repository import RoomRepository
from . import ServiceError

# Variables constantes para las reglas de negocio de reservas
ACTIVE_STATUSES = ("confirmed", "checked_in")   # reservas que ocupan la habitación / cuentan como "activas"
MAX_ACTIVE_RESERVATIONS = 3                     # máximo de reservas activas por huésped
LONG_STAY_NIGHTS = 7                            # una semana completa o más...
LONG_STAY_DISCOUNT = 0.10                       # ...10 % de descuento sobre el total
LATE_CANCEL_HOURS = 48                          # cancelar con menos de 48 h cobra la primera noche
MAX_NIGHTS = 30                                 # estadía máxima por reserva
MAX_ADVANCE_DAYS = 365                          # anticipación máxima para reservar

STATUS_LABELS = {"confirmed": "confirmada", "checked_in": "hospedado", "checked_out": "finalizada", "cancelled": "cancelada"}


class ReservationService:
    def __init__(self):
        self.reservations = ReservationRepository()
        self.rooms = RoomRepository()
        self.guests = GuestRepository()

    def _label(self, reservation):
        return STATUS_LABELS.get(reservation.status, reservation.status)

    def list_reservations(self, status=None, guest_id=None):
        return self.reservations.list_filtered(status, guest_id)

    def get_reservation(self, reservation_id):
        reservation = self.reservations.get_by_id(reservation_id)
        if reservation is None:
            raise ServiceError("Reserva no encontrada", 404)
        return reservation

    def create_reservation(self, data):
        missing = [f for f in ("room_id", "guest_id", "check_in", "check_out", "guests_count") if data.get(f) in (None, "")]
        if missing:
            raise ServiceError(f"Faltan campos: {', '.join(missing)}", 400)

        try:
            room_id = int(data["room_id"])
            guest_id = int(data["guest_id"])
            check_in = date.fromisoformat(str(data["check_in"]))
            check_out = date.fromisoformat(str(data["check_out"]))
            guests_count = int(data["guests_count"])
        except (TypeError, ValueError):
            raise ServiceError("IDs y guests_count numéricos; fechas en formato AAAA-MM-DD", 400)

        room = self.rooms.get_by_id(room_id)
        if room is None:
            raise ServiceError("Habitación no encontrada", 404)
        guest = self.guests.get_by_id(guest_id)
        if guest is None:
            raise ServiceError("Huésped no encontrado", 404)

        # R5: habitación en mantenimiento
        if room.status != "available":
            raise ServiceError(f"La habitación {room.number} está en mantenimiento y no se puede reservar")

        # R3, R2, RN5: fechas coherentes y dentro de los límites
        if check_in < date.today():
            raise ServiceError("No se puede reservar para una fecha que ya pasó")
        if check_out <= check_in:
            raise ServiceError("La fecha de salida debe ser posterior a la de ingreso")
        if (check_out - check_in).days > MAX_NIGHTS:
            raise ServiceError(f"La estadía no puede superar {MAX_NIGHTS} noches")
        if (check_in - date.today()).days > MAX_ADVANCE_DAYS:
            raise ServiceError(f"No se puede reservar con más de {MAX_ADVANCE_DAYS} días de anticipación")

        # R4: capacidad de la habitación
        if guests_count < 1 or guests_count > room.capacity:
            raise ServiceError(f"La habitación {room.number} admite entre 1 y {room.capacity} huéspedes")

        # R1: sin doble reserva
        overlap = self.reservations.find_overlap(room.id, check_in, check_out, ACTIVE_STATUSES)
        if overlap:
            raise ServiceError(
                f"La habitación {room.number} ya está reservada del {overlap.check_in.isoformat()} "
                f"al {overlap.check_out.isoformat()}")

        # R10: máximo de reservas activas por huésped
        if self.reservations.count_by_guest(guest.id, ACTIVE_STATUSES) >= MAX_ACTIVE_RESERVATIONS:
            raise ServiceError(f"El huésped ya tiene {MAX_ACTIVE_RESERVATIONS} reservas activas")

        # R6: descuento por estadía larga
        nights = (check_out - check_in).days
        total_price = nights * room.price_per_night
        if nights >= LONG_STAY_NIGHTS:
            total_price *= (1 - LONG_STAY_DISCOUNT)

        return self.reservations.create(
            room=room, guest=guest, check_in=check_in, check_out=check_out,
            guests_count=guests_count, status="confirmed", total_price=round(total_price, 2),
        )

    def cancel_reservation(self, reservation_id):
        reservation = self.get_reservation(reservation_id)
        # R8: solo se cancelan reservas confirmadas
        if reservation.status != "confirmed":
            raise ServiceError(f"Solo se pueden cancelar reservas confirmadas (estado actual: {self._label(reservation)})")

        # R7: con menos de 48 h para el ingreso se cobra la primera noche; si no, no se cobra nada.
        hours_left = (datetime.combine(reservation.check_in, time.min) - datetime.now()) / timedelta(hours=1)
        room = self.rooms.get_by_id(reservation.room_id)
        charge = room.price_per_night if hours_left < LATE_CANCEL_HOURS else 0
        return self.reservations.update(reservation, status="cancelled", total_price=charge)

    def check_in_reservation(self, reservation_id):
        reservation = self.get_reservation(reservation_id)
        # R8, R9, RN3
        if reservation.status != "confirmed":
            raise ServiceError(f"Solo se puede hacer check-in de reservas confirmadas (estado actual: {self._label(reservation)})")
        if date.today() < reservation.check_in:
            raise ServiceError(f"No se puede hacer check-in antes del {reservation.check_in.isoformat()}")
        if date.today() >= reservation.check_out:
            raise ServiceError("La reserva ya venció")
        return self.reservations.update(reservation, status="checked_in")

    def check_out_reservation(self, reservation_id):
        reservation = self.get_reservation(reservation_id)
        # R8: solo se hace check-out de huéspedes con check-in
        if reservation.status != "checked_in":
            raise ServiceError(f"Solo se puede hacer check-out de huéspedes con check-in (estado actual: {self._label(reservation)})")
        return self.reservations.update(reservation, status="checked_out")
