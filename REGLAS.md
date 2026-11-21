# Reglas de negocio · Hotel Mirador

Reglas que se desprenden del relato de Lucía (gerente) y que el sistema no cumplía, en el orden en que aparecen en el relato.
Cuando una regla de validación no se cumple, la API responde **422** con `{ "error": "mensaje" }`.

| # | Regla | Momento | Endpoint | Estado |
|---|---|---|---|---|
| RN1 | Sin doble reserva | Crear reserva | `POST /api/reservations` | Implementada |
| RN2 | Fechas coherentes | Crear reserva | `POST /api/reservations` | Implementada |
| RN3 | Sin reservas en el pasado | Crear reserva | `POST /api/reservations` | Implementada |
| RN4 | Capacidad de la habitación | Crear reserva | `POST /api/reservations` | Implementada |
| RN5 | Habitación en mantenimiento | Crear reserva | `POST /api/reservations` | Implementada |
| RN6 | Descuento por estadía larga | Crear reserva | `POST /api/reservations` | Solo identificada |
| RN7 | Penalidad por cancelación tardía | Cancelar | `PATCH /api/reservations/:id/cancel` | Solo identificada |
| RN8 | Transiciones de estado válidas | Check-in, check-out, cancelar | `PATCH /api/reservations/:id/...` | Solo identificada |
| RN9 | Check-in desde la fecha de ingreso | Check-in | `PATCH /api/reservations/:id/check-in` | Solo identificada |
| RN10 | Límite de reservas activas | Crear reserva | `POST /api/reservations` | Solo identificada |

---

### RN1 · Sin doble reserva
**Regla:** al crear una reserva, no puede existir otra reserva de la misma habitación con estado `confirmed` o `checked_in` cuyas fechas se superpongan; dos reservas se superponen si `nuevo.check_in < existente.check_out` y `nuevo.check_out > existente.check_in`. El día de salida de una reserva puede ser el día de ingreso de otra.
**Si no se cumple:** `422 { "error": "La habitación 202 ya está reservada entre el 2026-12-01 y el 2026-12-08" }`
**Origen:** «vendimos dos veces la 202 para el mismo fin de semana».

### RN2 · Fechas coherentes
**Regla:** al crear una reserva, la fecha de salida (`check_out`) debe ser posterior a la fecha de ingreso (`check_in`); es decir, la reserva debe tener al menos una noche.
**Si no se cumple:** `422 { "error": "La fecha de salida debe ser posterior a la fecha de ingreso" }`
**Origen:** «cargó una reserva con la salida antes del ingreso y el sistema le calculó un total negativo».

### RN3 · Sin reservas en el pasado
**Regla:** al crear una reserva, la fecha de ingreso (`check_in`) debe ser igual o posterior a la fecha de hoy.
**Si no se cumple:** `422 { "error": "No se puede reservar para una fecha que ya pasó" }`
**Origen:** «registró una reserva para un día que ya había pasado».

### RN4 · Capacidad de la habitación
**Regla:** al crear una reserva, la cantidad de personas (`guests_count`) no puede superar la capacidad (`capacity`) de la habitación elegida.
**Si no se cumple:** `422 { "error": "La habitación 101 admite como máximo 1 persona(s)" }`
**Origen:** «reservó la 101, que es simple, para una familia de cinco».

### RN5 · Habitación en mantenimiento
**Regla:** al crear una reserva, la habitación debe tener estado `available`; no se puede reservar una habitación con estado `maintenance`.
**Si no se cumple:** `422 { "error": "La habitación 203 está en mantenimiento y no se puede reservar" }`
**Origen:** «La 203 está en refacción desde octubre. Aun así el sistema [...] la deja reservar».

### RN6 · Descuento por estadía larga
**Regla:** al crear una reserva de 7 noches o más, el total (`total_price`) es `noches × precio_por_noche × 0,90`; con menos de 7 noches no hay descuento.
**Respuesta:** no es una validación, así que no responde 422. La reserva se crea normalmente (`201`) con el total ya descontado. Ejemplo: 7 noches en la 202 (Bs 420) → `total_price: 2646` en lugar de 2940.
**Origen:** «A quienes se quedan una semana completa o más les hacemos el 10 % de descuento sobre el total».

### RN7 · Penalidad por cancelación tardía
**Regla:** al cancelar, se calculan los días que faltan para el ingreso (`check_in − fecha de hoy`). Si faltan menos de 2 días (menos de 48 horas), el total pasa a ser el precio de una noche de la habitación; si faltan 2 días o más, el total pasa a ser 0.
**Respuesta:** no responde 422 porque la cancelación se permite igual. Devuelve `200` con `status: "cancelled"` y el `total_price` actualizado (0 o el precio de la primera noche).
**Origen:** «si cancela cuando faltan menos de 48 horas para su ingreso, igual le cobramos la primera noche».

### RN8 · Transiciones de estado válidas
**Regla:** una reserva solo puede cambiar de estado así:
- **check-in:** solo si está `confirmed` → pasa a `checked_in`;
- **check-out:** solo si está `checked_in` → pasa a `checked_out`;
- **cancelar:** solo si está `confirmed` → pasa a `cancelled`.

Cualquier otra combinación se rechaza (por ejemplo, check-out de una reserva confirmada, o check-in de una cancelada).
**Si no se cumple:** `422 { "error": "No se puede hacer check-out: la reserva está Confirmada y aún no hizo check-in" }` (el mensaje indica la acción y el estado actual).
**Origen:** «un huésped con check-out que nunca había hecho check-in, y una reserva cancelada que después aparecía como hospedada».

### RN9 · Check-in desde la fecha de ingreso
**Regla:** al registrar el check-in, la fecha de hoy debe ser igual o posterior a la fecha de ingreso (`check_in`) de la reserva.
**Si no se cumple:** `422 { "error": "El check-in de esta reserva recién se puede hacer desde el 2026-11-28" }`
**Origen:** «nadie debería poder hacer check-in antes de la fecha de su reserva».

### RN10 · Límite de reservas activas
**Regla:** al crear una reserva, el huésped no puede tener ya 3 reservas activas (estado `confirmed` o `checked_in`); como máximo puede tener 3 a la vez.
**Si no se cumple:** `422 { "error": "Ana Rojas ya tiene 3 reservas activas, que es el máximo permitido" }`
**Origen:** «nadie tenga más de tres reservas activas al mismo tiempo».
