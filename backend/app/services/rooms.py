from ..repositories import rooms as room_repository
from .errors import ConflictError, NotFoundError, ValidationError

ROOM_TYPES = ("single", "double", "family", "suite")
ROOM_STATUSES = ("available", "maintenance")


def list_rooms(status=None):
    return room_repository.list_rooms(status)


def get_room(room_id):
    room = room_repository.get_room(room_id)
    if room is None:
        raise NotFoundError("Habitación no encontrada")
    return room


def create_room(data):
    missing = [f for f in ("number", "type", "price_per_night", "capacity") if data.get(f) in (None, "")]
    if missing:
        raise ValidationError(f"Faltan campos: {', '.join(missing)}")
    if data["type"] not in ROOM_TYPES:
        raise ValidationError(f"Tipo inválido. Usa: {', '.join(ROOM_TYPES)}")

    try:
        price = float(data["price_per_night"])
        capacity = int(data["capacity"])
    except (TypeError, ValueError, OverflowError):
        raise ValidationError("price_per_night y capacity deben ser números")

    number = str(data["number"]).strip()
    if room_repository.get_room_by_number(number):
        raise ConflictError("Ya existe una habitación con ese número")

    room = room_repository.create_room(
        number=number,
        type=data["type"],
        price_per_night=price,
        capacity=capacity,
        status=data.get("status", "available"),
    )
    return room


def update_room(room_id, data):
    room = get_room(room_id)

    if "type" in data:
        if data["type"] not in ROOM_TYPES:
            raise ValidationError(f"Tipo inválido. Usa: {', '.join(ROOM_TYPES)}")
    if "status" in data:
        if data["status"] not in ROOM_STATUSES:
            raise ValidationError(f"Estado inválido. Usa: {', '.join(ROOM_STATUSES)}")
    try:
        price = float(data["price_per_night"]) if "price_per_night" in data else room.price_per_night
        capacity = int(data["capacity"]) if "capacity" in data else room.capacity
    except (TypeError, ValueError, OverflowError):
        raise ValidationError("price_per_night y capacity deben ser números")

    if "type" in data:
        room.type = data["type"]
    if "status" in data:
        room.status = data["status"]
    room.price_per_night = price
    room.capacity = capacity
    return room_repository.save_room(room)


def delete_room(room_id):
    room = get_room(room_id)
    if room_repository.room_has_reservations(room.id):
        raise ConflictError("La habitación tiene reservas registradas")
    room_repository.delete_room(room)
