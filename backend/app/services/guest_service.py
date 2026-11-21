from ..repositories.guest_repositories import (
    create_guest as repo_create_guest,
    delete_guest as repo_delete_guest,
    get_guest as repo_get_guest,
    get_guest_by_email,
    list_guests as repo_list_guests,
)


def list_guests():
    return repo_list_guests()


def get_guest(guest_id):
    guest = repo_get_guest(guest_id)
    if guest is None:
        return {"error": "Huésped no encontrado", "status": 404}
    return guest


def create_guest(data):
    data = data or {}
    missing = [f for f in ("full_name", "email", "document") if not str(data.get(f, "")).strip()]
    if missing:
        return {"error": f"Faltan campos: {', '.join(missing)}", "status": 400}

    email = data["email"].strip().lower()
    if "@" not in email:
        return {"error": "Email inválido", "status": 400}
    if get_guest_by_email(email):
        return {"error": "Ya existe un huésped con ese email", "status": 409}

    return repo_create_guest(
        full_name=data["full_name"].strip(),
        email=email,
        document=str(data["document"]).strip(),
    )


def delete_guest(guest_id):
    guest = repo_get_guest(guest_id)
    if guest is None:
        return {"error": "Huésped no encontrado", "status": 404}
    if guest.reservations:
        return {"error": "El huésped tiene reservas registradas", "status": 409}

    repo_delete_guest(guest)
    return {"deleted": True}