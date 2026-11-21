# Reglas de negocio · Hotel Mirador

Estas cinco reglas se validan al crear una reserva (`POST /api/reservations`), antes de guardarla. Si se incumple alguna, la API responde **422**, devuelve únicamente `{"error": "mensaje"}` y no registra la reserva.

## 1. Fechas ordenadas

**Regla:** Al crear una reserva, la fecha de salida debe ser posterior a la fecha de ingreso; una estadía debe tener al menos una noche.

**Respuesta:** 422 con `{"error": "La fecha de salida debe ser posterior a la fecha de ingreso"}`.

## 2. Ingreso sin fechas pasadas

**Regla:** Al crear una reserva, la fecha de ingreso debe ser igual o posterior al día actual del hotel, obtenido con la zona horaria `America/La_Paz`, independientemente de la zona horaria del servidor.

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

## Implementación y alcance

- Las validaciones y la selección de los estados que bloquean fechas viven en `backend/app/services/reservations.py`.
- La consulta de solapamientos vive en `backend/app/repositories/reservations.py`.
- `BusinessRuleError` representa los incumplimientos; `backend/app/api/error_handlers.py` los convierte a HTTP 422 en un solo lugar.
- Las pruebas de estas cinco reglas están en `backend/tests/test_reservation_rules.py`.
- Se conservan los modelos, las rutas y el JSON de éxito. Los errores existentes por campos faltantes, fechas mal formadas, entidades inexistentes y duplicados conservan sus códigos 400, 404 y 409.
- Quedan pendientes los descuentos, las penalidades de cancelación, las transiciones de estado, la fecha mínima del check-in y el máximo de tres reservas activas por huésped.
