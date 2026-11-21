from ..models import Reservation
from .base_repository import BaseRepository


class ReservationRepository(BaseRepository):
    model = Reservation

    def list(self, status=None, guest_id=None):
        query = Reservation.query
        if status:
            query = query.filter_by(status=status)
        if guest_id:
            query = query.filter_by(guest_id=guest_id)
        return query.order_by(Reservation.check_in).all()

    def find_overlapping(self, room_id, check_in, check_out, statuses):
        """Primera reserva de la habitación, en alguno de los estados dados,
        cuyas fechas se cruzan con el rango [check_in, check_out)."""
        return Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.status.in_(statuses),
            Reservation.check_in < check_out,
            Reservation.check_out > check_in,
        ).first()
