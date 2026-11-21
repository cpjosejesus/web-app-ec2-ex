# Reglas de negocio · Hotel Mirador

Estas siete reglas se validan en los servicios antes de crear una reserva (`POST /api/reservations`) o cambiar su estado (`PATCH /api/reservations/:id/...`), según corresponda. Si se incumple alguna, la API responde **422**, devuelve únicamente `{"error": "mensaje"}` y no crea ni modifica la reserva.

## 1. Fechas ordenadas

**Regla:** Al crear una reserva, la fecha de salida debe ser posterior a la fecha de ingreso; una estadía debe tener al menos una noche.

**Respuesta:** 422 con `{"error": "La fecha de salida debe ser posterior a la fecha de ingreso"}`.

## 2. Ingreso sin fechas pasadas

**Regla:** Al crear una reserva, la fecha de ingreso debe ser igual o posterior al día actual del hotel, obtenido con la zona horaria configurada en `HOTEL_TIMEZONE`, independientemente de las zonas horarias del servidor y de la persona que reserva.

`HOTEL_TIMEZONE` identifica la ubicación del hotel y utiliza `America/La_Paz` como valor inicial configurable. Una persona desde cualquier país puede reservar: las fechas `AAAA-MM-DD` representan días de estadía en el hotel, se conservan tal como se seleccionaron y no se convierten a UTC ni a la zona del visitante.

**Respuesta:** 422 con `{"error": "La fecha de ingreso no puede ser anterior a hoy"}`.

## 3. Capacidad de habitación

**Regla:** Al crear una reserva, la cantidad de personas debe representar un entero positivo y no superar la capacidad registrada de la habitación seleccionada; los valores booleanos no representan una cantidad de personas.

**Respuesta:** 422 con `{"error": "La cantidad de personas debe ser un entero entre 1 y la capacidad de la habitación (2)"}`; el número entre paréntesis se reemplaza por la capacidad real de la habitación.

## 4. Habitación habilitada

**Regla:** Al crear una reserva, el estado actual de la habitación seleccionada debe ser `available`; mientras esté en mantenimiento no se permiten nuevas reservas, incluso para fechas futuras.

**Respuesta:** 422 con `{"error": "La habitación está en mantenimiento y no se puede reservar"}`.

Las habitaciones en mantenimiento se conservan en la tabla de administración, pero no se ofrecen en el selector de nueva reserva; el backend también rechaza los intentos directos de reservarlas.

## 5. Reservas sin solapamiento

**Regla:** Al crear una reserva, no debe existir otra reserva de la misma habitación en estado `confirmed` o `checked_in` cuyo ingreso sea anterior a la nueva salida y cuya salida sea posterior al nuevo ingreso.

**Respuesta:** 422 con `{"error": "La habitación ya tiene una reserva para las fechas seleccionadas"}`.

El día de salida no ocupa la habitación: una reserva del 10 al 15 permite otra desde el 15. Las reservas `cancelled` y `checked_out` no bloquean fechas; las reservas de otras habitaciones tampoco.

## 6. Transiciones válidas

**Regla:** Al cancelar, registrar el ingreso o registrar la salida, el estado actual de la reserva debe permitir la acción: solo se permite `confirmed → cancelled`, `confirmed → checked_in` y `checked_in → checked_out`; se rechazan las demás transiciones, incluidas las acciones repetidas.

**Respuestas:**

- Cancelar desde un estado distinto de `confirmed`: 422 con `{"error": "Solo se puede cancelar una reserva confirmada"}`.
- Registrar ingreso desde un estado distinto de `confirmed`: 422 con `{"error": "Solo se puede registrar el ingreso de una reserva confirmada"}`.
- Registrar salida desde un estado distinto de `checked_in`: 422 con `{"error": "Solo se puede registrar la salida de una reserva con check-in"}`.

Las reservas canceladas y finalizadas no admiten ninguna de estas acciones. Una reserva con check-in ya no puede cancelarse. Esta regla no restringe todavía la fecha del check-in.

## 7. Máximo de tres reservas activas

**Regla:** Al crear una reserva, el huésped debe tener menos de tres reservas en estado `confirmed` o `checked_in`, contando todas sus habitaciones y fechas; si ya tiene tres o más, se rechaza la nueva reserva.

**Respuesta:** 422 con `{"error": "El huésped ya tiene tres reservas activas"}`.

Las reservas `cancelled` y `checked_out` no cuentan. Cancelar una reserva confirmada o finalizar una reserva hospedada libera un lugar para crear otra. Las reservas de otros huéspedes no cuentan para este límite.

## Implementación y alcance

- Las validaciones y la selección de los estados que bloquean fechas viven en `backend/app/services/reservations.py`.
- La consulta de solapamientos y el conteo de reservas viven en `backend/app/repositories/reservations.py`; el servicio determina los estados que cuentan y el límite permitido.
- `BusinessRuleError` representa los incumplimientos; `backend/app/api/error_handlers.py` los convierte a HTTP 422 en un solo lugar.
- Las pruebas de estas siete reglas están en `backend/tests/test_reservation_rules.py`.
- Se conservan los modelos, las rutas y el JSON de éxito. Los errores existentes por campos faltantes, fechas mal formadas, entidades inexistentes y duplicados conservan sus códigos 400, 404 y 409.
- Quedan pendientes los descuentos, las penalidades de cancelación y la fecha mínima del check-in.
