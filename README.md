# Hotel Mirador · web-app-ec2-ex

Sistema de recepción de un hotel: habitaciones, huéspedes y reservas.

- `backend/`: API REST en Flask con arquitectura por capas y SQLite.
- `frontend/`: HTML, CSS y JavaScript sin frameworks.

Todo corre con Docker Compose: el backend usa el servidor de desarrollo de Flask y el frontend el servidor estático de Python. No hay nginx ni gunicorn.

## Levantar el proyecto

```bash
docker compose up --build
```

| Servicio | URL |
|---|---|
| Frontend | http://localhost:8081 |
| API | http://localhost:8000/api |
| Salud | http://localhost:8000/api/health |

En una EC2 se usan las mismas URL con la IP pública (abrir los puertos 8081 y 8000 en el security group). La capa de API del frontend usa el mismo host desde el que se abrió la página.

La primera vez se cargan datos de ejemplo. Para empezar con la base vacía:

```bash
docker compose down -v
```

El código de las dos carpetas está montado en los contenedores: al guardar un archivo del backend, Flask se recarga solo; en el frontend basta con refrescar el navegador.

## Pruebas

```bash
docker compose exec backend pytest -q
```

## Estructura del backend

- `app/api/` mantiene un Blueprint por entidad con funciones de rutas: recibe solicitudes, llama a los servicios y devuelve JSON. `error_handlers.py` traduce las excepciones de negocio a HTTP.
- `app/services/` contiene funciones por entidad con sus casos de uso y reglas de negocio; no importa Flask.
- `app/repositories/` contiene funciones para consultar y persistir datos con `Model.query` y `db.session`.
- `app/models/` define las entidades y su mapeo a tablas con SQLAlchemy.
- `app/views/` convierte las entidades al formato JSON de la API.
- `app/__init__.py` configura Flask y registra los Blueprints de habitaciones, huéspedes y reservas.
- Dependencias de ejecución `api → services → repositories → models`.

## Estructura del frontend

- `index.html`: único HTML; enlaza la base de estilos y un CSS por bloque.
- `api.js`: único archivo con `fetch`; centraliza URL, headers, errores y operaciones de la API.
- `app.js`: formularios, pestañas y tablas; utiliza las funciones de `HotelApi` y muestra sus errores.
- `css/base.css`: variables, reset y tipografía. Los demás CSS definen los bloques BEM, sus elementos y modificadores (`tabs__button--active`, `button--danger`).
- Los identificadores se mantienen para JavaScript; los estilos usan clases BEM sin selectores por ID ni descendientes.
- Los totales se muestran desde `total_price` devuelto por el backend, también después de cambiar el estado de una reserva. Los descuentos y penalidades se calculan en los servicios del backend cuando se implementen sus reglas.

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
