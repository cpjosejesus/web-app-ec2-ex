from ..models import Room
from ..repositories import RoomRepository
from .exceptions import ConflictError, NotFoundError, ValidationError

ROOM_TYPES = ("single", "double", "family", "suite")
ROOM_STATUSES = ("available", "maintenance")


class RoomService:
    def __init__(self, rooms=None):
        self.rooms = rooms or RoomRepository()

    def list(self, status=None):
        return self.rooms.list(status=status)

    def get(self, room_id):
        room = self.rooms.get(room_id)
        if room is None:
            raise NotFoundError("Habitación no encontrada")
        return room

    def create(self, data):
        missing = [f for f in ("number", "type", "price_per_night", "capacity") if data.get(f) in (None, "")]
        if missing:
            raise ValidationError(f"Faltan campos: {', '.join(missing)}")
        self._validate_type(data["type"])

        try:
            price = float(data["price_per_night"])
            capacity = int(data["capacity"])
        except (TypeError, ValueError):
            raise ValidationError("price_per_night y capacity deben ser números")

        number = str(data["number"]).strip()
        if self.rooms.find_by_number(number):
            raise ConflictError("Ya existe una habitación con ese número")

        room = Room(
            number=number,
            type=data["type"],
            price_per_night=price,
            capacity=capacity,
            status=data.get("status", "available"),
        )
        return self.rooms.save(room)

    def update(self, room_id, data):
        room = self.get(room_id)

        if "type" in data:
            self._validate_type(data["type"])
            room.type = data["type"]
        if "status" in data:
            if data["status"] not in ROOM_STATUSES:
                raise ValidationError(f"Estado inválido. Usa: {', '.join(ROOM_STATUSES)}")
            room.status = data["status"]
        try:
            if "price_per_night" in data:
                room.price_per_night = float(data["price_per_night"])
            if "capacity" in data:
                room.capacity = int(data["capacity"])
        except (TypeError, ValueError):
            raise ValidationError("price_per_night y capacity deben ser números")

        self.rooms.commit()
        return room

    def delete(self, room_id):
        room = self.get(room_id)
        if room.reservations:
            raise ConflictError("La habitación tiene reservas registradas")
        self.rooms.delete(room)

    @staticmethod
    def _validate_type(room_type):
        if room_type not in ROOM_TYPES:
            raise ValidationError(f"Tipo inválido. Usa: {', '.join(ROOM_TYPES)}")
