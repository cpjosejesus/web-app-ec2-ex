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


def create_reservation(room, guest, check_in, check_out, guests_count, total_price, status="confirmed"):
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


def update_reservation_status(reservation, status):
    reservation.status = status
    db.session.commit()
    return reservation

def cancel_reservation(reservation):
    return update_reservation_status(reservation, "Cancelada")


def check_in_reservation(reservation):
    return update_reservation_status(reservation, "Hospedado")


def check_out_reservation(reservation):
    return update_reservation_status(reservation, "Finalizada")