from datetime import date

from ..repository.reservation_repository import ReservationRepository
from ..repository.room_repository import RoomRepository
from . import ServiceError

ROOM_TYPES = ("single", "double", "family", "suite")
ROOM_STATUSES = ("available", "maintenance")
ACTIVE_STATUSES = ("confirmed", "checked_in")


class RoomService:
    def __init__(self):
        self.rooms = RoomRepository()
        self.reservations = ReservationRepository()

    def list_rooms(self, status=None):
        return self.rooms.list_ordered(status)

    def get_room(self, room_id):
        room = self.rooms.get_by_id(room_id)
        if room is None:
            raise ServiceError("Habitación no encontrada", 404)
        return room

    def _validate_type(self, room_type):
        if room_type not in ROOM_TYPES:
            raise ServiceError(f"Tipo inválido. Usa: {', '.join(ROOM_TYPES)}", 400)

    def _validate_status(self, status):
        if status not in ROOM_STATUSES:
            raise ServiceError(f"Estado inválido. Usa: {', '.join(ROOM_STATUSES)}", 400)

    def _parse_price(self, value):
        try:
            price = float(value)
        except (TypeError, ValueError):
            raise ServiceError("price_per_night y capacity deben ser números", 400)
        if price <= 0:
            raise ServiceError("price_per_night debe ser > 0", 400)
        return price

    def _parse_capacity(self, value):
        try:
            capacity = int(value)
        except (TypeError, ValueError):
            raise ServiceError("price_per_night y capacity deben ser números", 400)
        if capacity < 1:
            raise ServiceError("capacity debe ser >= 1", 400)
        return capacity

    def create_room(self, data):
        missing = [f for f in ("number", "type", "price_per_night", "capacity") if data.get(f) in (None, "")]
        if missing:
            raise ServiceError(f"Faltan campos: {', '.join(missing)}", 400)
        self._validate_type(data["type"])
        price = self._parse_price(data["price_per_night"])
        capacity = self._parse_capacity(data["capacity"])
        status = data.get("status", "available")
        self._validate_status(status)

        number = str(data["number"]).strip()
        if self.rooms.find_by_number(number):
            raise ServiceError("Ya existe una habitación con ese número", 409)

        return self.rooms.create(number=number, type=data["type"], price_per_night=price, capacity=capacity, status=status)

    def update_room(self, room_id, data):
        room = self.get_room(room_id)
        changes = {}

        if "type" in data:
            self._validate_type(data["type"])
            changes["type"] = data["type"]

        if "status" in data:
            self._validate_status(data["status"])
            # RN1: no pasar a mantenimiento con reservas activas
            if data["status"] == "maintenance":
                active = [r for r in self.reservations.list_by_room(room.id, ACTIVE_STATUSES)
                          if r.check_out > date.today()]
                if active:
                    detail = ", ".join(f"#{r.id} ({r.check_in} a {r.check_out})" for r in active)
                    raise ServiceError(f"La habitación {room.number} tiene reservas activas: {detail}")
            changes["status"] = data["status"]

        if "price_per_night" in data:
            changes["price_per_night"] = self._parse_price(data["price_per_night"])

        if "capacity" in data:
            capacity = self._parse_capacity(data["capacity"])
            # RN2: no reducir la capacidad por debajo de lo reservado
            over = [r for r in self.reservations.list_by_room(room.id, ACTIVE_STATUSES) if r.guests_count > capacity]
            if over:
                detail = ", ".join(f"#{r.id} ({r.guests_count} huéspedes)" for r in over)
                raise ServiceError(f"La capacidad no puede ser menor a las reservas activas: {detail}")
            changes["capacity"] = capacity

        return self.rooms.update(room, **changes)

    def delete_room(self, room_id):
        room = self.get_room(room_id)
        if self.reservations.list_by_room(room.id):
            raise ServiceError("La habitación tiene reservas registradas", 409)
        self.rooms.delete(room)
