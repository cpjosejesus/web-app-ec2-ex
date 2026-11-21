# Nuevas reglas de negocio

Todas viven en la capa de servicios (`backend/app/services/`). Cuando una regla no se cumple, el servicio lanza `ServiceError(mensaje)` (por defecto `422`) y `create_app` lo convierte en `{"error": "<mensaje>"}`.

### RN1: No se puede poner una habitación en mantenimiento si este cuenta con reservas posteriores a hoy día

**services/room_service.py**: en el método `RoomService.update_room`
```python
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
```

### RN2: No reducir la capacidad de una habitacion por debajo de lo que se ha reservado

**services/room_service.py**: en el método `RoomService.update_room`
```python
if "capacity" in data:
    capacity = self._parse_capacity(data["capacity"])
    # RN2: no reducir la capacidad por debajo de lo reservado
    over = [r for r in self.reservations.list_by_room(room.id, ACTIVE_STATUSES) if r.guests_count > capacity]
    if over:
        detail = ", ".join(f"#{r.id} ({r.guests_count} huéspedes)" for r in over)
        raise ServiceError(f"La capacidad no puede ser menor a las reservas activas: {detail}")
    changes["capacity"] = capacity
```

### RN3: Check-in fuera de plazo (no-show)

**services/reservation_service.py**: en el método `ReservationService.check_in_reservation`
```python
if date.today() >= reservation.check_out:
    raise ServiceError("La reserva ya venció")
```

### RN4: Documento de huésped único

**services/guest_service.py**: en el método `GuestService.create_guest` (responde `409`, como los demás duplicados)
```python
document = str(data["document"]).strip()
if self.guests.find_by_document(document):
    raise ServiceError("Ya existe un huésped con ese documento", 409)

return self.guests.create(full_name=str(data["full_name"]).strip(), email=email, document=document)
```

### RN5: Límites de estadía y anticipación, Al crear una reserva, se rechaza si tiene más de 30 noches o si check_in está a más de 365 días de hoy

Nuevas variables constantes en **services/reservation_service.py**:
```python
MAX_NIGHTS = 30                                 # estadía máxima por reserva
MAX_ADVANCE_DAYS = 365                          # anticipación máxima para reservar
```

**services/reservation_service.py**: en el método `ReservationService.create_reservation`
```python
if (check_out - check_in).days > MAX_NIGHTS:
    raise ServiceError(f"La estadía no puede superar {MAX_NIGHTS} noches")
if (check_in - date.today()).days > MAX_ADVANCE_DAYS:
    raise ServiceError(f"No se puede reservar con más de {MAX_ADVANCE_DAYS} días de anticipación")
```
