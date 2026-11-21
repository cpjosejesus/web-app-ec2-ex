# Reglas de negocio — Hotel Mirador

Cuando una regla no se cumple, la API responde `422 Unprocessable Entity` con `{"error": "<mensaje>"}`.

Las reglas viven en la capa de servicios (`backend/app/services/`). Cuando una no se cumple, el servicio lanza `ServiceError(mensaje)` y `create_app` lo convierte en la respuesta JSON con su código.

## R1. Sin doble reserva
**Regla:** Al crear una reserva (`POST /api/reservations`), se rechaza si la misma habitación ya tiene otra reserva en estado `confirmed` o `checked_in` cuyo rango de fechas se solapa con el nuevo (`check_in` existente < `check_out` nuevo y `check_out` existente > `check_in` nuevo).
**Dónde:** `backend/app/services/reservation_service.py` → `ReservationService.create_reservation` (usa `ReservationRepository.find_overlap`).
**Si no se cumple:** `422 Unprocessable Entity` — `"La habitación <número> ya está reservada del <AAAA-MM-DD> al <AAAA-MM-DD>"`.

## R2. Salida posterior al ingreso
**Regla:** Al crear una reserva, `check_out` debe ser estrictamente posterior a `check_in` (mínimo una noche).
**Dónde:** `backend/app/services/reservation_service.py` → `ReservationService.create_reservation`.
**Si no se cumple:** `422 Unprocessable Entity` — `"La fecha de salida debe ser posterior a la de ingreso"`.

## R3. Sin fechas pasadas
**Regla:** Al crear una reserva, `check_in` debe ser igual o posterior a la fecha actual del servidor.
**Dónde:** `backend/app/services/reservation_service.py` → `ReservationService.create_reservation`.
**Si no se cumple:** `422 Unprocessable Entity` — `"No se puede reservar para una fecha que ya pasó"`.

## R4. Capacidad de la habitación
**Regla:** Al crear una reserva, `guests_count` debe estar entre 1 y el `capacity` de la habitación solicitada.
**Dónde:** `backend/app/services/reservation_service.py` → `ReservationService.create_reservation`.
**Si no se cumple:** `422 Unprocessable Entity` — `"La habitación <número> admite entre 1 y <capacidad> huéspedes"`.

## R5. Habitación en mantenimiento
**Regla:** Al crear una reserva, la habitación debe tener `status = "available"`; una habitación en `maintenance` no se puede reservar.
**Dónde:** `backend/app/services/reservation_service.py` → `ReservationService.create_reservation`.
**Si no se cumple:** `422 Unprocessable Entity` — `"La habitación <número> está en mantenimiento y no se puede reservar"`.

## R6. Descuento por estadía larga
**Regla:** Al crear una reserva, si la cantidad de noches (`check_out − check_in`) es 7 o más, `total_price` se calcula como `noches × price_per_night × 0.90`; en otro caso, `noches × price_per_night`.
**Dónde:** `backend/app/services/reservation_service.py` → `ReservationService.create_reservation` (constantes `LONG_STAY_NIGHTS` y `LONG_STAY_DISCOUNT`).
**Si no se cumple:** no aplica (es un cálculo); la reserva se crea con `201 Created` y el `total_price` ya descontado.

## R7. Cobro por cancelación tardía
**Regla:** Al cancelar una reserva (`PATCH /api/reservations/<id>/cancel`), si faltan menos de 48 horas para las 00:00 del día de `check_in`, `total_price` pasa a ser el precio de una noche (`price_per_night`); si faltan 48 horas o más, `total_price` pasa a ser 0.
**Dónde:** `backend/app/services/reservation_service.py` → `ReservationService.cancel_reservation` (constante `LATE_CANCEL_HOURS`).
**Si no se cumple:** no aplica (es un cálculo); responde `200 OK` con la reserva en estado `cancelled` y el monto cobrado en `total_price`.

## R8. Transiciones de estado válidas
**Regla:** El estado de una reserva solo puede cambiar así: `confirmed → checked_in` (check-in), `checked_in → checked_out` (check-out) y `confirmed → cancelled` (cancelación); cualquier otra transición se rechaza.
**Dónde:** `backend/app/services/reservation_service.py` → `ReservationService.cancel_reservation`, `check_in_reservation` y `check_out_reservation`.
**Si no se cumple:** `422 Unprocessable Entity` — p. ej. `"Solo se puede hacer check-out de huéspedes con check-in (estado actual: <estado>)"`.

## R9. Check-in no anticipado
**Regla:** Al hacer check-in (`PATCH /api/reservations/<id>/check-in`), la fecha actual del servidor debe ser igual o posterior a `check_in` de la reserva.
**Dónde:** `backend/app/services/reservation_service.py` → `ReservationService.check_in_reservation`.
**Si no se cumple:** `422 Unprocessable Entity` — `"No se puede hacer check-in antes del <AAAA-MM-DD>"`.

## R10. Máximo de reservas activas por huésped
**Regla:** Al crear una reserva, el huésped no puede tener ya 3 o más reservas en estado `confirmed` o `checked_in`.
**Dónde:** `backend/app/services/reservation_service.py` → `ReservationService.create_reservation` (usa `ReservationRepository.count_by_guest`; constante `MAX_ACTIVE_RESERVATIONS`).
**Si no se cumple:** `422 Unprocessable Entity` — `"El huésped ya tiene 3 reservas activas"`.
