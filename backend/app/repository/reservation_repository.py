from ..models import Reservation
from .repository import Repository


class ReservationRepository(Repository):
    model = Reservation

    def list_filtered(self, status=None, guest_id=None):
        query = Reservation.query
        if status:
            query = query.filter_by(status=status)
        if guest_id:
            query = query.filter_by(guest_id=guest_id)
        return query.order_by(Reservation.check_in).all()

    def find_overlap(self, room_id, check_in, check_out, statuses):
        """Primera reserva de la habitación cuyo rango se solapa con [check_in, check_out)."""
        return Reservation.query.filter(
            Reservation.room_id == room_id,
            Reservation.status.in_(statuses),
            Reservation.check_in < check_out,
            Reservation.check_out > check_in,
        ).first()

    def list_by_room(self, room_id, statuses=None):
        query = Reservation.query.filter(Reservation.room_id == room_id)
        if statuses:
            query = query.filter(Reservation.status.in_(statuses))
        return query.all()

    def count_by_guest(self, guest_id, statuses=None):
        query = Reservation.query.filter(Reservation.guest_id == guest_id)
        if statuses:
            query = query.filter(Reservation.status.in_(statuses))
        return query.count()
