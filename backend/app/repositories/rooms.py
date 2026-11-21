from ..models import Reservation, Room, db


def list_rooms(status=None):
    query = Room.query
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Room.number).all()


def get_room(room_id):
    return db.session.get(Room, room_id)


def get_room_by_number(number):
    return Room.query.filter_by(number=number).first()


def room_has_reservations(room_id):
    return Reservation.query.filter_by(room_id=room_id).first() is not None


def create_room(number, type, price_per_night, capacity, status):
    room = Room(
        number=number,
        type=type,
        price_per_night=price_per_night,
        capacity=capacity,
        status=status,
    )
    db.session.add(room)
    db.session.commit()
    return room


def save_room(room):
    db.session.commit()
    return room


def delete_room(room):
    db.session.delete(room)
    db.session.commit()
