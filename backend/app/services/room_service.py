from ..repositories.room_repositories import (
    create_room as repo_create_room,
    delete_room as repo_delete_room,
    get_room as repo_get_room,
    get_room_by_number,
    list_rooms as repo_list_rooms,
    update_room as repo_update_room,
)

ROOM_TYPES = ("Simple", "Doble", "Familiar", "Suite")
ROOM_STATUSES = ("Disponible", "Mantenimiento")


def list_rooms(status=None):
    return repo_list_rooms(status=status)


def get_room(room_id):
    room = repo_get_room(room_id)
    if room is None:
        return {"error": "Habitación no encontrada", "status": 404}
    return room


def create_room(data):
    data = data or {}
    missing = [f for f in ("number", "type", "price_per_night", "capacity") if data.get(f) in (None, "")]
    if missing:
        return {"error": f"Faltan campos: {', '.join(missing)}", "status": 400}
    if data["type"] not in ROOM_TYPES:
        return {"error": f"Tipo inválido. Usa: {', '.join(ROOM_TYPES)}", "status": 400}

    try:
        price = float(data["price_per_night"])
        capacity = int(data["capacity"])
    except (TypeError, ValueError):
        return {"error": "price_per_night y capacity deben ser números", "status": 400}

    if price <= 0 or capacity <= 0:
        return {"error": "El precio por noche y la capacidad deben ser mayores a cero", "status": 422}

    number = str(data["number"]).strip()
    if get_room_by_number(number):
        return {"error": "Ya existe una habitación con ese número", "status": 409}

    status = data.get("status", "Disponible")
    if status not in ROOM_STATUSES:
        return {"error": f"Estado inválido. Usa: {', '.join(ROOM_STATUSES)}", "status": 400}

    return repo_create_room(
        number=number,
        room_type=data["type"],
        price_per_night=price,
        capacity=capacity,
        status=status,
    )


def update_room(room_id, data):
    room = repo_get_room(room_id)
    if room is None:
        return {"error": "Habitación no encontrada", "status": 404}

    data = data or {}
    room_type = None
    if "type" in data:
        if data["type"] not in ROOM_TYPES:
            return {"error": f"Tipo inválido. Usa: {', '.join(ROOM_TYPES)}", "status": 400}
        room_type = data["type"]

    status = None
    if "status" in data:
        if data["status"] not in ROOM_STATUSES:
            return {"error": f"Estado inválido. Usa: {', '.join(ROOM_STATUSES)}", "status": 400}
        status = data["status"]

    price = None
    capacity = None
    try:
        if "price_per_night" in data:
            price = float(data["price_per_night"])
            if price <= 0:
                return {"error": "El precio por noche debe ser mayor a cero", "status": 422}
        if "capacity" in data:
            capacity = int(data["capacity"])
            if capacity <= 0:
                return {"error": "La capacidad debe ser mayor a cero", "status": 422}
    except (TypeError, ValueError):
        return {"error": "price_per_night y capacity deben ser números", "status": 400}

    return repo_update_room(
        room,
        room_type=room_type,
        status=status,
        price_per_night=price,
        capacity=capacity,
    )


def delete_room(room_id):
    room = repo_get_room(room_id)
    if room is None:
        return {"error": "Habitación no encontrada", "status": 404}
    if room.reservations:
        return {"error": "La habitación tiene reservas registradas", "status": 409}

    repo_delete_room(room)
    return {"deleted": True}