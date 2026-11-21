from ..models import Guest, Reservation, db


def list_guests():
    return Guest.query.order_by(Guest.full_name).all()


def get_guest(guest_id):
    return db.session.get(Guest, guest_id)


def get_guest_by_email(email):
    return Guest.query.filter_by(email=email).first()


def guest_has_reservations(guest_id):
    return Reservation.query.filter_by(guest_id=guest_id).first() is not None


def create_guest(full_name, email, document):
    guest = Guest(full_name=full_name, email=email, document=document)
    db.session.add(guest)
    db.session.commit()
    return guest


def delete_guest(guest):
    db.session.delete(guest)
    db.session.commit()
