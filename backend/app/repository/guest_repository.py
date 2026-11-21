from ..models import Guest
from .repository import Repository


class GuestRepository(Repository):
    model = Guest

    def list_ordered(self):
        return Guest.query.order_by(Guest.full_name).all()

    def find_by_email(self, email):
        return Guest.query.filter_by(email=email).first()

    def find_by_document(self, document):
        return Guest.query.filter_by(document=document).first()
