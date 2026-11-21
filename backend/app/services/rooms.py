from .errors import ConflictError, NotFoundError, ValidationError

ROOM_TYPES = ("single", "double", "family", "suite")
ROOM_STATUSES = ("available", "maintenance")


class RoomService:
    def __init__(self, repository):
        self.repository = repository

    def list_rooms(self, status=None):
        return self.repository.list_rooms(status)

    def get_room(self, room_id):
        room = self.repository.get_room(room_id)
        if room is None:
            raise NotFoundError("Habitación no encontrada")
        return room

    def create_room(self, data):
        required = ("number", "type", "price_per_night", "capacity")
        missing = [field for field in required if data.get(field) in (None, "")]
        if missing:
            raise ValidationError(f"Faltan campos: {', '.join(missing)}")

        self._validate_type(data["type"])
        fields = self._numeric_fields(data)
        number = str(data["number"]).strip()

        if self.repository.get_room_by_number(number) is not None:
            raise ConflictError("Ya existe una habitación con ese número")

        return self.repository.create_room(
            number=number,
            type=data["type"],
            status=data.get("status", "available"),
            **fields,
        )

    def update_room(self, room_id, data):
        room = self.get_room(room_id)
        fields = {}

        if "type" in data:
            self._validate_type(data["type"])
            fields["type"] = data["type"]

        if "status" in data:
            if data["status"] not in ROOM_STATUSES:
                raise ValidationError(f"Estado inválido. Usa: {', '.join(ROOM_STATUSES)}")
            fields["status"] = data["status"]

        fields.update(self._numeric_fields(data))
        return self.repository.update_room(room, **fields)

    def delete_room(self, room_id):
        room = self.get_room(room_id)
        if self.repository.room_has_reservations(room.id):
            raise ConflictError("La habitación tiene reservas registradas")
        self.repository.delete_room(room)

    def _validate_type(self, room_type):
        if room_type not in ROOM_TYPES:
            raise ValidationError(f"Tipo inválido. Usa: {', '.join(ROOM_TYPES)}")

    def _numeric_fields(self, data):
        fields = {}
        try:
            if "price_per_night" in data:
                fields["price_per_night"] = float(data["price_per_night"])
            if "capacity" in data:
                fields["capacity"] = int(data["capacity"])
        except (TypeError, ValueError, OverflowError) as error:
            raise ValidationError("price_per_night y capacity deben ser números") from error
        return fields
