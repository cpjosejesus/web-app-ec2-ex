from ..repositories import guests as guest_repository
from .errors import ConflictError, NotFoundError, ValidationError


def list_guests():
    return guest_repository.list_guests()


def get_guest(guest_id):
    guest = guest_repository.get_guest(guest_id)
    if guest is None:
        raise NotFoundError("Huésped no encontrado")
    return guest


def create_guest(data):
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

    if guest_repository.get_guest_by_email(email) is not None:
        raise ConflictError("Ya existe un huésped con ese email")

    return guest_repository.create_guest(
        full_name=full_name.strip(),
        email=email,
        document=str(data["document"]).strip(),
    )


def delete_guest(guest_id):
    guest = get_guest(guest_id)
    if guest_repository.guest_has_reservations(guest.id):
        raise ConflictError("El huésped tiene reservas registradas")
    guest_repository.delete_guest(guest)
