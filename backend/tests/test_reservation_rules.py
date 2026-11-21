from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfoNotFoundError

import pytest

from app import create_app
from app.services import reservations as reservation_service


@pytest.fixture
def hotel_today(monkeypatch, app):
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # En UTC ya es 2 de enero; en La Paz todavía es 1 de enero.
            instant = datetime(2030, 1, 2, 2, 0, tzinfo=timezone.utc)
            return instant.astimezone(tz)

    monkeypatch.setattr(reservation_service, "datetime", FixedDatetime)
    app.config["HOTEL_TIMEZONE"] = "America/La_Paz"
    return date(2030, 1, 1)


@pytest.fixture
def reservation_data(room, guest, hotel_today):
    start = hotel_today + timedelta(days=10)
    return {
        "room_id": room["id"],
        "guest_id": guest["id"],
        "check_in": start.isoformat(),
        "check_out": (start + timedelta(days=5)).isoformat(),
        "guests_count": 2,
    }


def assert_rule_error(client, response, message, reservation_count=0):
    assert response.status_code == 422
    assert response.get_json() == {"error": message}
    assert len(client.get("/api/reservations").get_json()) == reservation_count


@pytest.mark.parametrize("nights", [-1, 0])
def test_check_out_must_be_after_check_in(client, reservation_data, nights):
    start = date.fromisoformat(reservation_data["check_in"])
    reservation_data["check_out"] = (start + timedelta(days=nights)).isoformat()

    response = client.post("/api/reservations", json=reservation_data)

    assert_rule_error(client, response, "La fecha de salida debe ser posterior a la fecha de ingreso")


def test_past_check_in_is_rejected(client, reservation_data, hotel_today):
    reservation_data["check_in"] = (hotel_today - timedelta(days=1)).isoformat()

    response = client.post("/api/reservations", json=reservation_data)

    assert_rule_error(client, response, "La fecha de ingreso no puede ser anterior a hoy")


def test_today_in_la_paz_is_allowed_even_when_utc_is_tomorrow(client, reservation_data, hotel_today):
    reservation_data["check_in"] = hotel_today.isoformat()
    reservation_data["check_out"] = (hotel_today + timedelta(days=1)).isoformat()

    response = client.post("/api/reservations", json=reservation_data)

    assert response.status_code == 201
    assert response.get_json()["check_in"] == "2030-01-01"
    assert response.get_json()["nights"] == 1
    assert response.get_json()["total_price"] == 300


@pytest.mark.parametrize("hotel_timezone,expected_status", [
    ("America/La_Paz", 201),
    ("America/Los_Angeles", 201),
    ("Europe/Madrid", 422),
    ("Asia/Tokyo", 422),
])
def test_past_dates_use_the_configured_hotel_timezone(
    app, client, reservation_data, hotel_timezone, expected_status,
):
    app.config["HOTEL_TIMEZONE"] = hotel_timezone
    reservation_data["check_in"] = "2030-01-01"
    reservation_data["check_out"] = "2030-01-03"

    response = client.post("/api/reservations", json=reservation_data)

    assert response.status_code == expected_status
    if expected_status == 201:
        assert response.get_json()["check_in"] == "2030-01-01"
        assert response.get_json()["check_out"] == "2030-01-03"
    else:
        assert_rule_error(client, response, "La fecha de ingreso no puede ser anterior a hoy")


@pytest.mark.parametrize("visitor_timezone", ["Asia/Tokyo", "Europe/Madrid", "America/Los_Angeles"])
def test_a_visitor_cannot_override_the_hotel_timezone(client, reservation_data, visitor_timezone):
    reservation_data["check_in"] = "2030-01-01"
    reservation_data["check_out"] = "2030-01-03"

    response = client.post(
        "/api/reservations", json=reservation_data,
        headers={"X-Timezone": visitor_timezone},
    )

    assert response.status_code == 201
    assert response.get_json()["check_in"] == "2030-01-01"
    assert response.get_json()["check_out"] == "2030-01-03"


def test_invalid_hotel_timezone_is_rejected_at_startup():
    with pytest.raises(ZoneInfoNotFoundError):
        create_app({"HOTEL_TIMEZONE": "Invalid/Timezone"})


@pytest.mark.parametrize("count", [3, 0, -1, 1.5, "1.5", "dos", True, False])
def test_guest_count_must_be_an_integer_within_capacity(client, reservation_data, count):
    reservation_data["guests_count"] = count

    response = client.post("/api/reservations", json=reservation_data)

    assert_rule_error(
        client, response,
        "La cantidad de personas debe ser un entero entre 1 y la capacidad de la habitación (2)",
    )


@pytest.mark.parametrize("count", [1, 2, "2"])
def test_guest_count_within_capacity_is_allowed(client, reservation_data, count):
    reservation_data["guests_count"] = count

    response = client.post("/api/reservations", json=reservation_data)

    assert response.status_code == 201
    assert response.get_json()["guests_count"] == int(count)


def test_room_in_maintenance_cannot_be_reserved(client, room, reservation_data):
    updated = client.put(f"/api/rooms/{room['id']}", json={"status": "maintenance"})
    assert updated.status_code == 200

    response = client.post("/api/reservations", json=reservation_data)

    assert_rule_error(client, response, "La habitación está en mantenimiento y no se puede reservar")


def test_room_can_be_reserved_after_maintenance_ends(client, room, reservation_data):
    client.put(f"/api/rooms/{room['id']}", json={"status": "maintenance"})
    client.put(f"/api/rooms/{room['id']}", json={"status": "available"})

    response = client.post("/api/reservations", json=reservation_data)

    assert response.status_code == 201


@pytest.mark.parametrize("status", ["confirmed", "checked_in"])
@pytest.mark.parametrize("start_offset,end_offset", [(0, 5), (1, 4), (-1, 6), (-1, 1), (4, 6)])
def test_overlapping_active_reservations_are_rejected(
    client, reservation_data, status, start_offset, end_offset,
):
    existing = client.post("/api/reservations", json=reservation_data)
    assert existing.status_code == 201
    if status == "checked_in":
        rid = existing.get_json()["id"]
        assert client.patch(f"/api/reservations/{rid}/check-in").status_code == 200

    start = date.fromisoformat(reservation_data["check_in"])
    reservation_data["check_in"] = (start + timedelta(days=start_offset)).isoformat()
    reservation_data["check_out"] = (start + timedelta(days=end_offset)).isoformat()

    response = client.post("/api/reservations", json=reservation_data)

    assert_rule_error(
        client, response,
        "La habitación ya tiene una reserva para las fechas seleccionadas",
        reservation_count=1,
    )


@pytest.mark.parametrize("start_offset,end_offset", [(-3, 0), (5, 8)])
def test_consecutive_reservations_are_allowed(client, reservation_data, start_offset, end_offset):
    assert client.post("/api/reservations", json=reservation_data).status_code == 201
    start = date.fromisoformat(reservation_data["check_in"])
    reservation_data["check_in"] = (start + timedelta(days=start_offset)).isoformat()
    reservation_data["check_out"] = (start + timedelta(days=end_offset)).isoformat()

    response = client.post("/api/reservations", json=reservation_data)

    assert response.status_code == 201


@pytest.mark.parametrize("status", ["cancelled", "checked_out"])
def test_inactive_reservations_do_not_block_dates(client, reservation_data, status):
    created = client.post("/api/reservations", json=reservation_data)
    assert created.status_code == 201
    rid = created.get_json()["id"]
    if status == "cancelled":
        assert client.patch(f"/api/reservations/{rid}/cancel").status_code == 200
    else:
        assert client.patch(f"/api/reservations/{rid}/check-in").status_code == 200
        assert client.patch(f"/api/reservations/{rid}/check-out").status_code == 200

    response = client.post("/api/reservations", json=reservation_data)

    assert response.status_code == 201


def test_other_rooms_do_not_block_dates(client, reservation_data):
    assert client.post("/api/reservations", json=reservation_data).status_code == 201
    another_room = client.post("/api/rooms", json={
        "number": "102", "type": "double", "price_per_night": 300, "capacity": 2,
    })
    assert another_room.status_code == 201
    reservation_data["room_id"] = another_room.get_json()["id"]

    response = client.post("/api/reservations", json=reservation_data)

    assert response.status_code == 201


@pytest.mark.parametrize("status", ["confirmed", "checked_in", "checked_out", "cancelled"])
@pytest.mark.parametrize("action,required_status,new_status,message", [
    ("cancel", "confirmed", "cancelled", "Solo se puede cancelar una reserva confirmada"),
    ("check-in", "confirmed", "checked_in", "Solo se puede registrar el ingreso de una reserva confirmada"),
    ("check-out", "checked_in", "checked_out", "Solo se puede registrar la salida de una reserva con check-in"),
])
def test_only_valid_reservation_transitions_are_allowed(
    client, reservation_data, status, action, required_status, new_status, message,
):
    created = client.post("/api/reservations", json=reservation_data)
    assert created.status_code == 201
    rid = created.get_json()["id"]

    if status == "cancelled":
        assert client.patch(f"/api/reservations/{rid}/cancel").status_code == 200
    elif status in ("checked_in", "checked_out"):
        assert client.patch(f"/api/reservations/{rid}/check-in").status_code == 200
        if status == "checked_out":
            assert client.patch(f"/api/reservations/{rid}/check-out").status_code == 200

    before = client.get(f"/api/reservations/{rid}").get_json()
    response = client.patch(f"/api/reservations/{rid}/{action}")

    if status == required_status:
        assert response.status_code == 200
        assert response.get_json() == {**before, "status": new_status}
        assert client.get(f"/api/reservations/{rid}").get_json() == response.get_json()
    else:
        assert_rule_error(client, response, message, reservation_count=1)
        assert client.get(f"/api/reservations/{rid}").get_json() == before


def post_reservation_at_offset(client, data, days):
    start = date.fromisoformat(data["check_in"])
    end = date.fromisoformat(data["check_out"])
    return client.post("/api/reservations", json={
        **data,
        "check_in": (start + timedelta(days=days)).isoformat(),
        "check_out": (end + timedelta(days=days)).isoformat(),
    })


@pytest.mark.parametrize("checked_in_count", [0, 1, 3])
def test_fourth_active_reservation_is_rejected(client, reservation_data, checked_in_count):
    for index in range(3):
        created = post_reservation_at_offset(client, reservation_data, index * 10)
        assert created.status_code == 201
        if index < checked_in_count:
            rid = created.get_json()["id"]
            assert client.patch(f"/api/reservations/{rid}/check-in").status_code == 200

    response = post_reservation_at_offset(client, reservation_data, 30)

    assert_rule_error(client, response, "El huésped ya tiene tres reservas activas", reservation_count=3)


@pytest.mark.parametrize("inactive_status", ["cancelled", "checked_out"])
def test_cancelling_or_finishing_a_reservation_frees_one_place(client, reservation_data, inactive_status):
    for index in range(3):
        created = post_reservation_at_offset(client, reservation_data, index * 10)
        assert created.status_code == 201
    rid = created.get_json()["id"]
    if inactive_status == "cancelled":
        assert client.patch(f"/api/reservations/{rid}/cancel").status_code == 200
    else:
        assert client.patch(f"/api/reservations/{rid}/check-in").status_code == 200
        assert client.patch(f"/api/reservations/{rid}/check-out").status_code == 200

    allowed = post_reservation_at_offset(client, reservation_data, 30)
    assert allowed.status_code == 201

    rejected = post_reservation_at_offset(client, reservation_data, 40)
    assert_rule_error(client, rejected, "El huésped ya tiene tres reservas activas", reservation_count=4)


def test_other_guests_reservations_do_not_count_towards_the_limit(client, reservation_data):
    for index in range(3):
        assert post_reservation_at_offset(client, reservation_data, index * 10).status_code == 201
    another_guest = client.post("/api/guests", json={
        "full_name": "Luis Pérez", "email": "luis@example.com", "document": "456",
    })
    assert another_guest.status_code == 201
    reservation_data["guest_id"] = another_guest.get_json()["id"]

    response = post_reservation_at_offset(client, reservation_data, 30)

    assert response.status_code == 201
    assert response.get_json()["guest_id"] == another_guest.get_json()["id"]


def test_guest_limit_counts_reservations_across_different_rooms(client, reservation_data):
    assert client.post("/api/reservations", json=reservation_data).status_code == 201
    for index in range(3):
        room = client.post("/api/rooms", json={
            "number": str(200 + index), "type": "double", "price_per_night": 300, "capacity": 2,
        })
        assert room.status_code == 201
        reservation_data["room_id"] = room.get_json()["id"]
        response = client.post("/api/reservations", json=reservation_data)
        if index < 2:
            assert response.status_code == 201
        else:
            assert_rule_error(client, response, "El huésped ya tiene tres reservas activas", reservation_count=3)
