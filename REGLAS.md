Reglas de Negocio del Sistema

Las siguientes reglas definen las validaciones de negocio aplicadas en la capa de servicios para la gestión de reservas y estados asociados.

1. Sin reservas en fecha pasada

Regla: Al crear una reserva, se valida que la fecha de ingreso (check_in) no sea anterior a la fecha actual (date.today()) utilizando check_in y la fecha del día al momento de registrar la reserva.

Respuesta de la API: HTTP 422 con el cuerpo {"error": "No se puede registrar una reserva en una fecha pasada"}.

2. Salida posterior al ingreso

Regla: Al crear una reserva, se valida que la fecha de salida (check_out) sea estrictamente posterior a la fecha de ingreso (check_in) utilizando ambas fechas enviadas en la solicitud al momento de crear la reserva.

Respuesta de la API: HTTP 422 con el cuerpo {"error": "La fecha de salida debe ser posterior a la fecha de ingreso"}.

3. Habitación no disponible por mantenimiento

Regla: Al crear una reserva, se valida que la habitación consultada (room.status) no se encuentre en estado "Mantenimiento" utilizando el estado actual de la habitación asociada a room_id al momento de registrar la reserva.

Respuesta de la API: HTTP 422 con el cuerpo {"error": "La habitación está en mantenimiento y no puede reservarse"}.

4. Capacidad mínima y máxima de huéspedes

Regla: Al crear una reserva, se valida que la cantidad de huéspedes (guests_count) sea mayor o igual a 1 y no supere la capacidad máxima de la habitación (room.capacity) utilizando guests_count de la solicitud y room.capacity de la habitación al momento de registrar la reserva.

Respuesta de la API: HTTP 422 con {"error": "La cantidad de huéspedes debe ser al menos 1"} si guests_count <= 0, o {"error": "La cantidad de huéspedes (<guests_count>) supera la capacidad de la habitación (<room.capacity>)"} si excede la capacidad.

5. Reserva cancelada inmutable

Regla: Al cancelar, hacer check-in o hacer check-out de una reserva existente, se valida que su estado actual (reservation.status) no sea "Cancelada" utilizando el estado registrado de la reserva identificada por reservation_id al momento de solicitar el cambio de estado.

Respuesta de la API: HTTP 422 con el cuerpo {"error": "No se puede modificar una reserva cancelada"}.