from . import commit
from ..models import Reservation, Room, db


class RoomRepository:
    def list_rooms(self, status=None):
        query = Room.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Room.number).all()

    def get_room(self, room_id):
        return db.session.get(Room, room_id)

    def get_room_by_number(self, number):
        return Room.query.filter_by(number=number).first()

    def room_has_reservations(self, room_id):
        return Reservation.query.filter_by(room_id=room_id).first() is not None

    def create_room(self, **fields):
        room = Room(**fields)
        db.session.add(room)
        commit()
        return room

    def update_room(self, room, **fields):
        for field, value in fields.items():
            setattr(room, field, value)
        commit()
        return room

    def delete_room(self, room):
        db.session.delete(room)
        commit()
