from ..models import Room, db


def list_rooms(status=None):
    query = Room.query
    if status:
        query = query.filter_by(status=status)
    return query.order_by(Room.number).all()


def get_room(room_id):
    return db.session.get(Room, room_id)


def create_room(number, room_type, price_per_night, capacity, status="Disponible"):
    room = Room(
        number=number,
        type=room_type,
        price_per_night=price_per_night,
        capacity=capacity,
        status=status,
    )
    db.session.add(room)
    db.session.commit()
    return room


def update_room(room, room_type=None, status=None, price_per_night=None, capacity=None):
    if room_type is not None:
        room.type = room_type
    if status is not None:
        room.status = status
    if price_per_night is not None:
        room.price_per_night = price_per_night
    if capacity is not None:
        room.capacity = capacity
    db.session.commit()
    return room


def delete_room(room):
    db.session.delete(room)
    db.session.commit()

def get_room_by_number(number):
    return Room.query.filter_by(number=number).first()