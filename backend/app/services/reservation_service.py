from datetime import date

from ..models import Reservation
from ..repositories import GuestRepository, ReservationRepository, RoomRepository
from .exceptions import BusinessRuleError, NotFoundError, ValidationError

REQUIRED_FIELDS = ("room_id", "guest_id", "check_in", "check_out", "guests_count")
# Estados en los que una reserva ocupa la habitación.
ACTIVE_STATUSES = ("confirmed", "checked_in")


class ReservationService:
    """Casos de uso de las reservas. Aquí viven las reglas de negocio (REGLAS.md)."""

    def __init__(self, reservations=None, rooms=None, guests=None):
        self.reservations = reservations or ReservationRepository()
        self.rooms = rooms or RoomRepository()
        self.guests = guests or GuestRepository()

    def list(self, status=None, guest_id=None):
        return self.reservations.list(status=status, guest_id=guest_id)

    def get(self, reservation_id):
        reservation = self.reservations.get(reservation_id)
        if reservation is None:
            raise NotFoundError("Reserva no encontrada")
        return reservation

    def create(self, data):
        missing = [f for f in REQUIRED_FIELDS if data.get(f) in (None, "")]
        if missing:
            raise ValidationError(f"Faltan campos: {', '.join(missing)}")

        room = self.rooms.get(int(data["room_id"]))
        if room is None:
            raise NotFoundError("Habitación no encontrada")
        guest = self.guests.get(int(data["guest_id"]))
        if guest is None:
            raise NotFoundError("Huésped no encontrado")

        try:
            check_in = date.fromisoformat(data["check_in"])
            check_out = date.fromisoformat(data["check_out"])
            guests_count = int(data["guests_count"])
        except (TypeError, ValueError):
            raise ValidationError("Fechas en formato AAAA-MM-DD y guests_count numérico")

        self._check_room_available(room)                 # RN5
        self._check_capacity(room, guests_count)         # RN4
        self._check_dates(check_in, check_out)           # RN2 y RN3
        self._check_no_overlap(room, check_in, check_out)  # RN1

        nights = (check_out - check_in).days
        total_price = nights * room.price_per_night

        reservation = Reservation(
            room=room,
            guest=guest,
            check_in=check_in,
            check_out=check_out,
            guests_count=guests_count,
            status="confirmed",
            total_price=total_price,
        )
        return self.reservations.save(reservation)

    # --- Reglas de negocio al crear una reserva (ver REGLAS.md) ---

    def _check_no_overlap(self, room, check_in, check_out):
        """RN1 · Sin doble reserva."""
        existing = self.reservations.find_overlapping(room.id, check_in, check_out, ACTIVE_STATUSES)
        if existing:
            raise BusinessRuleError(
                f"La habitación {room.number} ya está reservada entre el "
                f"{existing.check_in.isoformat()} y el {existing.check_out.isoformat()}"
            )

    @staticmethod
    def _check_dates(check_in, check_out):
        """RN2 · Fechas coherentes y RN3 · Sin reservas en el pasado."""
        if check_out <= check_in:
            raise BusinessRuleError("La fecha de salida debe ser posterior a la fecha de ingreso")
        if check_in < date.today():
            raise BusinessRuleError("No se puede reservar para una fecha que ya pasó")

    @staticmethod
    def _check_capacity(room, guests_count):
        """RN4 · Capacidad de la habitación."""
        if guests_count > room.capacity:
            raise BusinessRuleError(
                f"La habitación {room.number} admite como máximo {room.capacity} persona(s)"
            )

    @staticmethod
    def _check_room_available(room):
        """RN5 · Habitación en mantenimiento."""
        if room.status == "maintenance":
            raise BusinessRuleError(
                f"La habitación {room.number} está en mantenimiento y no se puede reservar"
            )

    # --- Cambios de estado ---

    def cancel(self, reservation_id):
        return self._change_status(reservation_id, "cancelled")

    def check_in(self, reservation_id):
        return self._change_status(reservation_id, "checked_in")

    def check_out(self, reservation_id):
        return self._change_status(reservation_id, "checked_out")

    def _change_status(self, reservation_id, new_status):
        reservation = self.get(reservation_id)
        reservation.status = new_status
        self.reservations.commit()
        return reservation
