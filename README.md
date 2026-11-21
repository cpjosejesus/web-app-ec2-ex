# Hotel Mirador · web-app-ec2-ex

Sistema de recepción de un hotel: habitaciones, huéspedes y reservas.

- `backend/`: API REST en Flask con **arquitectura por capas** (rutas → servicios → repositorios → modelos) y SQLite.
- `frontend/`: HTML, CSS y JavaScript sin frameworks.

Todo corre con Docker Compose: el backend usa el servidor de desarrollo de Flask y el frontend el servidor estático de Python. No hay nginx ni gunicorn.

## Levantar el proyecto

```bash
docker compose up --build
```

| Servicio | URL |
|---|---|
| Frontend | http://localhost:8080 |
| API | http://localhost:8000/api |
| Salud | http://localhost:8000/api/health |

En una EC2 se usan las mismas URL con la IP pública (abrir los puertos 8080 y 8000 en el security group). El frontend arma la URL de la API con el mismo host desde el que se abrió la página.

La primera vez se cargan datos de ejemplo. Para empezar con la base vacía:

```bash
docker compose down -v
```

El código de las dos carpetas está montado en los contenedores: al guardar un archivo del backend, Flask se recarga solo; en el frontend basta con refrescar el navegador.

## Pruebas

```bash
docker compose exec backend pytest -q
```

## Estructura (arquitectura por capas)

```
backend/app/
├── routes/         presentación: lee la petición, llama al servicio, devuelve JSON y código HTTP
├── views/          presentación: cómo se representa cada entidad en JSON (lo usan las rutas)
├── services/       casos de uso y reglas de negocio (REGLAS.md); no importa flask
│   └── exceptions.py   errores propios: ValidationError, NotFoundError, ConflictError, BusinessRuleError
├── repositories/   guardar y consultar datos; único lugar con db.session y Model.query
├── models/         entidades y su mapeo a tablas (Flask-SQLAlchemy); no conocen a las capas de arriba
├── errors.py       único lugar donde los errores propios se traducen a HTTP (400, 404, 409, 422)
├── __init__.py     create_app: config, CORS, blueprints, manejadores de error, seed
└── seed.py         datos de ejemplo
```

Las dependencias van en una sola dirección: rutas → servicios → repositorios → modelos. Un servicio lanza una excepción propia y `errors.py` la convierte en `{ "error": "..." }` con su código.

## API

| Método | Ruta | Descripción |
|---|---|---|
| GET | `/api/rooms?status=` | lista de habitaciones |
| GET | `/api/rooms/:id` | una habitación |
| POST | `/api/rooms` | crea `{ number, type, price_per_night, capacity }` |
| PUT | `/api/rooms/:id` | modifica `type`, `status`, `price_per_night` o `capacity` |
| DELETE | `/api/rooms/:id` | elimina (409 si tiene reservas) |
| GET | `/api/guests` | lista de huéspedes |
| GET | `/api/guests/:id` | un huésped |
| POST | `/api/guests` | crea `{ full_name, email, document }` |
| DELETE | `/api/guests/:id` | elimina (409 si tiene reservas) |
| GET | `/api/reservations?status=&guest_id=` | lista de reservas |
| GET | `/api/reservations/:id` | una reserva |
| POST | `/api/reservations` | crea `{ room_id, guest_id, check_in, check_out, guests_count }` |
| PATCH | `/api/reservations/:id/cancel` | cancela |
| PATCH | `/api/reservations/:id/check-in` | registra el ingreso |
| PATCH | `/api/reservations/:id/check-out` | registra la salida |

Valores válidos:

- `type`: `single`, `double`, `family`, `suite`.
- `status` de habitación: `available`, `maintenance`.
- `status` de reserva: `confirmed`, `checked_in`, `checked_out`, `cancelled`.
- Fechas en formato `AAAA-MM-DD`; precios en bolivianos.

Los errores se devuelven como `{ "error": "mensaje" }` con el código HTTP correspondiente.
