from datetime import date, datetime, timedelta, timezone

import pytest

from app.services import reservations as reservation_service


@pytest.fixture
def hotel_today(monkeypatch):
    class FixedDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            # En UTC ya es 2 de enero; en La Paz todavía es 1 de enero.
            instant = datetime(2030, 1, 2, 2, 0, tzinfo=timezone.utc)
            return instant.astimezone(tz)

    monkeypatch.setattr(reservation_service, "datetime", FixedDatetime)
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
