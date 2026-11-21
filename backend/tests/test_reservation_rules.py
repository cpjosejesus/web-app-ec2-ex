from datetime import date, timedelta

import pytest

from app import create_app
from app.models import Guest, Reservation, Room, db


@pytest.fixture
def client():
    app = create_app(
        {
            "TESTING": True,
            "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
            "SEED": False,
        }
    )

    with app.app_context():
        db.create_all()

        room = Room(
            number="101",
            room_type="Simple",
            capacity=2,
            price_per_night=200,
            status="Disponible",
        )
        maint_room = Room(
            number="102",
            room_type="Doble",
            capacity=2,
            price_per_night=250,
            status="Mantenimiento",
        )
        guest = Guest(full_name="Lucía Vargas", email="lucia@example.com")

        db.session.add_all([room, maint_room, guest])
        db.session.commit()

        ids = {
            "room_id": room.id,
            "maint_room_id": maint_room.id,
            "guest_id": guest.id,
        }

    with app.test_client() as test_client:
        test_client.ids = ids
        yield test_client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_regla_1_fecha_ingreso_pasada(client):
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today = date.today().isoformat()

    res = client.post(
        "/api/reservations",
        json={
            "room_id": client.ids["room_id"],
            "guest_id": client.ids["guest_id"],
            "check_in": yesterday,
            "check_out": today,
            "guests_count": 1,
        },
    )

    assert res.status_code == 422
    assert "error" in res.get_json()


def test_regla_2_salida_no_posterior_a_ingreso(client):
    check_in = (date.today() + timedelta(days=2)).isoformat()
    check_out = check_in  # misma fecha (no es posterior)

    res = client.post(
        "/api/reservations",
        json={
            "room_id": client.ids["room_id"],
            "guest_id": client.ids["guest_id"],
            "check_in": check_in,
            "check_out": check_out,
            "guests_count": 1,
        },
    )

    assert res.status_code == 422
    assert "error" in res.get_json()


def test_regla_3_habitacion_en_mantenimiento(client):
    check_in = (date.today() + timedelta(days=2)).isoformat()
    check_out = (date.today() + timedelta(days=4)).isoformat()

    res = client.post(
        "/api/reservations",
        json={
            "room_id": client.ids["maint_room_id"],
            "guest_id": client.ids["guest_id"],
            "check_in": check_in,
            "check_out": check_out,
            "guests_count": 1,
        },
    )

    assert res.status_code == 422
    assert "error" in res.get_json()


def test_regla_4_supera_capacidad_habitacion(client):
    check_in = (date.today() + timedelta(days=2)).isoformat()
    check_out = (date.today() + timedelta(days=4)).isoformat()

    res = client.post(
        "/api/reservations",
        json={
            "room_id": client.ids["room_id"],
            "guest_id": client.ids["guest_id"],
            "check_in": check_in,
            "check_out": check_out,
            "guests_count": 5,  # room capacity is 2
        },
    )

    assert res.status_code == 422
    assert "error" in res.get_json()


def test_regla_5_no_modificar_reserva_cancelada(client):
    check_in = date.today() + timedelta(days=2)
    check_out = date.today() + timedelta(days=4)

    created = client.post(
        "/api/reservations",
        json={
            "room_id": client.ids["room_id"],
            "guest_id": client.ids["guest_id"],
            "check_in": check_in.isoformat(),
            "check_out": check_out.isoformat(),
            "guests_count": 1,
        },
    )
    assert created.status_code == 201
    res_id = created.get_json()["id"]

    # Primera cancelación: válida
    first_cancel = client.patch(f"/api/reservations/{res_id}/cancel")
    assert first_cancel.status_code == 200

    # Segunda cancelación sobre reserva ya cancelada: debe dar 422
    second_cancel = client.patch(f"/api/reservations/{res_id}/cancel")
    assert second_cancel.status_code == 422
    assert "error" in second_cancel.get_json()