from ..models import Reservation, db


def list_reservations(status=None, guest_id=None):
    query = Reservation.query
    if status:
        query = query.filter_by(status=status)
    if guest_id:
        query = query.filter_by(guest_id=guest_id)
    return query.order_by(Reservation.check_in).all()


def get_reservation(reservation_id):
    return db.session.get(Reservation, reservation_id)


def find_overlapping_reservation(room_id, check_in, check_out, statuses):
    return Reservation.query.filter(
        Reservation.room_id == room_id,
        Reservation.status.in_(statuses),
        Reservation.check_in < check_out,
        Reservation.check_out > check_in,
    ).first()


def create_reservation(room, guest, check_in, check_out, guests_count, status, total_price):
    reservation = Reservation(
        room=room,
        guest=guest,
        check_in=check_in,
        check_out=check_out,
        guests_count=guests_count,
        status=status,
        total_price=total_price,
    )
    db.session.add(reservation)
    db.session.commit()
    return reservation


def save_reservation(reservation):
    db.session.commit()
    return reservation
