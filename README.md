# Hotel Mirador · web-app-ec2-ex

Sistema de recepción de un hotel: habitaciones, huéspedes y reservas.

- `backend/`: API REST en Flask con arquitectura **MVC** (models, views, controllers) y SQLite.
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

## Estructura (MVC)

```
backend/
├── run.py                     punto de entrada (flask --app run:app)
├── app/
│   ├── __init__.py            create_app: config, CORS, blueprints, seed
│   ├── config.py
│   ├── seed.py                datos de ejemplo
│   ├── models/                M: tablas con Flask-SQLAlchemy
│   ├── views/                 V: cómo se presenta cada modelo en JSON
│   └── controllers/           C: blueprints con las rutas
└── tests/
frontend/
├── index.html
├── style.css
└── app.js
```

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

## Arquitectura del Sistema

El backend del sistema de gestión hotelera está organizado en una **arquitectura en 4 capas** (**Rutas → Servicios → Repositorios → Modelos**), separando la capa HTTP de las reglas de negocio y del acceso a base de datos. El frontend se comunica con el backend mediante peticiones HTTP a la API REST (`fetch`).

### Estructura de carpetas

```text
proyecto/
├── README.md
├── REGLAS.md                  # Reglas de negocio documentadas y códigos de error HTTP
├── backend/
│   ├── app/
│   │   ├── __init__.py        # Fábrica de la aplicación (create_app) y registro de Blueprints
│   │   ├── config.py          # Configuración de entorno y base de datos
│   │   ├── models.py          # Modelos ORM (Room, Guest, Reservation)
│   │   ├── seed.py            # Datos iniciales opcionales
│   │   ├── routes/            # Capa HTTP: Blueprints de rooms, guests y reservations
│   │   ├── services/          # Capa de negocio: validaciones y reglas del dominio
│   │   └── repositories/      # Capa de persistencia: consultas y operaciones con db.session
│   └── tests/                 # Pruebas automatizadas con pytest
└── frontend/
    ├── index.html
    ├── app.js                 # Lógica de interfaz, estados y manejo de errores con try/catch
    └── api/
        └── api.js             # Cliente HTTP, manejo de 204 y extracción de errores (data.error)
