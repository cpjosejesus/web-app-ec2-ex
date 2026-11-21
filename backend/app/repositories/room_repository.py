from ..models import Room
from .base_repository import BaseRepository


class RoomRepository(BaseRepository):
    model = Room

    def list(self, status=None):
        query = Room.query
        if status:
            query = query.filter_by(status=status)
        return query.order_by(Room.number).all()

    def find_by_number(self, number):
        return Room.query.filter_by(number=number).first()
