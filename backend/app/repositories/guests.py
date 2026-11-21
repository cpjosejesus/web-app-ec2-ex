from . import commit
from ..models import Guest, Reservation, db


class GuestRepository:
    def list_guests(self):
        return Guest.query.order_by(Guest.full_name).all()

    def get_guest(self, guest_id):
        return db.session.get(Guest, guest_id)

    def get_guest_by_email(self, email):
        return Guest.query.filter_by(email=email).first()

    def guest_has_reservations(self, guest_id):
        return Reservation.query.filter_by(guest_id=guest_id).first() is not None

    def create_guest(self, **fields):
        guest = Guest(**fields)
        db.session.add(guest)
        commit()
        return guest

    def delete_guest(self, guest):
        db.session.delete(guest)
        commit()
