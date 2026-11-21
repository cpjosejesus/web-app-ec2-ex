from datetime import date

from .errors import NotFoundError, ValidationError


class ReservationService:
    def __init__(self, repository, room_service, guest_service):
        self.repository = repository
        self.room_service = room_service
        self.guest_service = guest_service

    def list_reservations(self, status=None, guest_id=None):
        return self.repository.list_reservations(status, guest_id)

    def get_reservation(self, reservation_id):
        reservation = self.repository.get_reservation(reservation_id)
        if reservation is None:
            raise NotFoundError("Reserva no encontrada")
        return reservation

    def create_reservation(self, data):
        required = ("room_id", "guest_id", "check_in", "check_out", "guests_count")
        missing = [field for field in required if data.get(field) in (None, "")]
        if missing:
            raise ValidationError(f"Faltan campos: {', '.join(missing)}")

        room = self.room_service.get_room(self._parse_id(data["room_id"], "room_id"))
        guest = self.guest_service.get_guest(self._parse_id(data["guest_id"], "guest_id"))

        try:
            check_in = date.fromisoformat(data["check_in"])
            check_out = date.fromisoformat(data["check_out"])
            guests_count = int(data["guests_count"])
        except (TypeError, ValueError, OverflowError) as error:
            raise ValidationError(
                "Fechas en formato AAAA-MM-DD y guests_count numérico"
            ) from error

        nights = (check_out - check_in).days
        return self.repository.create_reservation(
            room=room,
            guest=guest,
            check_in=check_in,
            check_out=check_out,
            guests_count=guests_count,
            status="confirmed",
            total_price=nights * room.price_per_night,
        )

    def cancel_reservation(self, reservation_id):
        return self._change_status(reservation_id, "cancelled")

    def check_in_reservation(self, reservation_id):
        return self._change_status(reservation_id, "checked_in")

    def check_out_reservation(self, reservation_id):
        return self._change_status(reservation_id, "checked_out")

    def _change_status(self, reservation_id, status):
        reservation = self.get_reservation(reservation_id)
        return self.repository.update_reservation_status(reservation, status)

    @staticmethod
    def _parse_id(value, field):
        try:
            return int(value)
        except (TypeError, ValueError, OverflowError) as error:
            raise ValidationError(f"{field} debe ser numérico") from error
