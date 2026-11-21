from . import commit
from ..models import Reservation, db


class ReservationRepository:
    def list_reservations(self, status=None, guest_id=None):
        query = Reservation.query
        if status:
            query = query.filter_by(status=status)
        if guest_id:
            query = query.filter_by(guest_id=guest_id)
        return query.order_by(Reservation.check_in).all()

    def get_reservation(self, reservation_id):
        return db.session.get(Reservation, reservation_id)

    def create_reservation(self, **fields):
        reservation = Reservation(**fields)
        db.session.add(reservation)
        commit()
        return reservation

    def update_reservation_status(self, reservation, status):
        reservation.status = status
        commit()
        return reservation
