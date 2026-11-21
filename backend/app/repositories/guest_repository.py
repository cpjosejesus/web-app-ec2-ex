from ..models import Guest
from .base_repository import BaseRepository


class GuestRepository(BaseRepository):
    model = Guest

    def list(self):
        return Guest.query.order_by(Guest.full_name).all()

    def find_by_email(self, email):
        return Guest.query.filter_by(email=email).first()
