from .errors import ConflictError, NotFoundError, ValidationError


class GuestService:
    def __init__(self, repository):
        self.repository = repository

    def list_guests(self):
        return self.repository.list_guests()

    def get_guest(self, guest_id):
        guest = self.repository.get_guest(guest_id)
        if guest is None:
            raise NotFoundError("Huésped no encontrado")
        return guest

    def create_guest(self, data):
        required = ("full_name", "email", "document")
        missing = [
            field for field in required
            if data.get(field) is None or not str(data[field]).strip()
        ]
        if missing:
            raise ValidationError(f"Faltan campos: {', '.join(missing)}")

        email = data["email"]
        if not isinstance(email, str) or "@" not in email:
            raise ValidationError("Email inválido")
        email = email.strip().lower()

        full_name = data["full_name"]
        if not isinstance(full_name, str):
            raise ValidationError("full_name debe ser texto")

        if self.repository.get_guest_by_email(email) is not None:
            raise ConflictError("Ya existe un huésped con ese email")

        return self.repository.create_guest(
            full_name=full_name.strip(),
            email=email,
            document=str(data["document"]).strip(),
        )

    def delete_guest(self, guest_id):
        guest = self.get_guest(guest_id)
        if self.repository.guest_has_reservations(guest.id):
            raise ConflictError("El huésped tiene reservas registradas")
        self.repository.delete_guest(guest)
