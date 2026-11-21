from ..models import Room
from .repository import Repository


class RoomRepository(Repository):
    model = Room

    def list_ordered(self, status=None):
        query = Room.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Room.number).all()

    def find_by_number(self, number):
        return Room.query.filter_by(number=number).first()
