from ..repository.guest_repository import GuestRepository
from ..repository.reservation_repository import ReservationRepository
from . import ServiceError


class GuestService:
    def __init__(self):
        self.guests = GuestRepository()
        self.reservations = ReservationRepository()

    def list_guests(self):
        return self.guests.list_ordered()

    def get_guest(self, guest_id):
        guest = self.guests.get_by_id(guest_id)
        if guest is None:
            raise ServiceError("Huésped no encontrado", 404)
        return guest

    def create_guest(self, data):
        missing = [f for f in ("full_name", "email", "document") if not str(data.get(f, "")).strip()]
        if missing:
            raise ServiceError(f"Faltan campos: {', '.join(missing)}", 400)

        email = str(data["email"]).strip().lower()
        if "@" not in email:
            raise ServiceError("Email inválido", 400)
        if self.guests.find_by_email(email):
            raise ServiceError("Ya existe un huésped con ese email", 409)

        document = str(data["document"]).strip()
        if self.guests.find_by_document(document):
            raise ServiceError("Ya existe un huésped con ese documento", 409)

        return self.guests.create(full_name=str(data["full_name"]).strip(), email=email, document=document)

    def delete_guest(self, guest_id):
        guest = self.get_guest(guest_id)
        if self.reservations.count_by_guest(guest.id):
            raise ServiceError("El huésped tiene reservas registradas", 409)
        self.guests.delete(guest)
