from ..models import Guest
from ..repositories import GuestRepository
from .exceptions import ConflictError, NotFoundError, ValidationError


class GuestService:
    def __init__(self, guests=None):
        self.guests = guests or GuestRepository()

    def list(self):
        return self.guests.list()

    def get(self, guest_id):
        guest = self.guests.get(guest_id)
        if guest is None:
            raise NotFoundError("Huésped no encontrado")
        return guest

    def create(self, data):
        missing = [f for f in ("full_name", "email", "document") if not str(data.get(f, "")).strip()]
        if missing:
            raise ValidationError(f"Faltan campos: {', '.join(missing)}")

        email = data["email"].strip().lower()
        if "@" not in email:
            raise ValidationError("Email inválido")
        if self.guests.find_by_email(email):
            raise ConflictError("Ya existe un huésped con ese email")

        guest = Guest(
            full_name=data["full_name"].strip(),
            email=email,
            document=str(data["document"]).strip(),
        )
        return self.guests.save(guest)

    def delete(self, guest_id):
        guest = self.get(guest_id)
        if guest.reservations:
            raise ConflictError("El huésped tiene reservas registradas")
        self.guests.delete(guest)
