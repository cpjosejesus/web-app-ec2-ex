from datetime import date, timedelta

import pytest

import app.services.reservation_service as reservation_service

TODAY = date.today()


def d(days):
    return (TODAY + timedelta(days=days)).isoformat()


@pytest.fixture
def reserve(client, room, guest):
    """Crea una reserva en la habitación 101 (capacidad 2, Bs 300/noche) y devuelve la respuesta."""
    def _reserve(start, end, guests_count=2, room_id=None, guest_id=None):
        return client.post("/api/reservations", json={
            "room_id": room_id or room["id"], "guest_id": guest_id or guest["id"],
            "check_in": d(start), "check_out": d(end), "guests_count": guests_count,
        })
    return _reserve


def fake_today(monkeypatch, days):
    """Hace que el servicio de reservas crea que hoy es TODAY + days."""
    class FakeDate(date):
        @classmethod
        def today(cls):
            return TODAY + timedelta(days=days)
    monkeypatch.setattr(reservation_service, "date", FakeDate)


# ---------- REGLAS.md ----------

def test_r1_sin_doble_reserva(reserve):
    assert reserve(10, 13).status_code == 201
    res = reserve(12, 15)
    assert res.status_code == 422
    assert "ya está reservada" in res.get_json()["error"]
    assert reserve(13, 15).status_code == 201  # empezar el día de salida de otra sí se puede


def test_r2_salida_posterior_al_ingreso(reserve):
    assert reserve(10, 8).status_code == 422
    assert reserve(10, 10).status_code == 422


def test_r3_sin_fechas_pasadas(reserve):
    res = reserve(-1, 2)
    assert res.status_code == 422
    assert "ya pasó" in res.get_json()["error"]


def test_r4_capacidad_de_la_habitacion(reserve):
    assert reserve(10, 12, guests_count=3).status_code == 422
    assert reserve(10, 12, guests_count=0).status_code == 422


def test_r5_habitacion_en_mantenimiento(client, room, reserve):
    client.put(f"/api/rooms/{room['id']}", json={"status": "maintenance"})
    res = reserve(10, 12)
    assert res.status_code == 422
    assert "mantenimiento" in res.get_json()["error"]


def test_r6_descuento_por_estadia_larga(reserve):
    assert reserve(10, 16).get_json()["total_price"] == 1800   # 6 noches: sin descuento
    assert reserve(20, 27).get_json()["total_price"] == 1890   # 7 noches: 2100 - 10 %


def test_r7_cobro_por_cancelacion_tardia(client, reserve):
    con_tiempo = reserve(10, 12).get_json()
    tardia = reserve(1, 3).get_json()
    assert client.patch(f"/api/reservations/{con_tiempo['id']}/cancel").get_json()["total_price"] == 0
    assert client.patch(f"/api/reservations/{tardia['id']}/cancel").get_json()["total_price"] == 300


def test_r8_transiciones_de_estado_validas(client, reserve):
    rid = reserve(0, 2).get_json()["id"]
    assert client.patch(f"/api/reservations/{rid}/check-out").status_code == 422  # sin check-in
    client.patch(f"/api/reservations/{rid}/cancel")
    assert client.patch(f"/api/reservations/{rid}/check-in").status_code == 422   # cancelada
    assert client.patch(f"/api/reservations/{rid}/cancel").status_code == 422     # ya cancelada


def test_r9_check_in_no_anticipado(client, reserve):
    rid = reserve(2, 4).get_json()["id"]
    res = client.patch(f"/api/reservations/{rid}/check-in")
    assert res.status_code == 422
    assert "antes del" in res.get_json()["error"]


def test_r10_maximo_tres_reservas_activas(reserve):
    for i in range(3):
        assert reserve(10 + i * 2, 11 + i * 2).status_code == 201
    res = reserve(30, 31)
    assert res.status_code == 422
    assert "3 reservas activas" in res.get_json()["error"]


# ---------- REGLAS_NUEVAS.md ----------

def test_rn1_mantenimiento_sin_reservas_activas(client, room, reserve):
    rid = reserve(10, 12).get_json()["id"]
    res = client.put(f"/api/rooms/{room['id']}", json={"status": "maintenance"})
    assert res.status_code == 422
    assert f"#{rid}" in res.get_json()["error"]
    client.patch(f"/api/reservations/{rid}/cancel")
    assert client.put(f"/api/rooms/{room['id']}", json={"status": "maintenance"}).status_code == 200


def test_rn2_no_reducir_capacidad_bajo_lo_reservado(client, room, reserve):
    reserve(10, 12, guests_count=2)
    assert client.put(f"/api/rooms/{room['id']}", json={"capacity": 1}).status_code == 422
    assert client.put(f"/api/rooms/{room['id']}", json={"capacity": 3}).status_code == 200


def test_rn3_check_in_fuera_de_plazo(client, reserve, monkeypatch):
    rid = reserve(0, 2).get_json()["id"]
    fake_today(monkeypatch, 2)  # hoy = día de check_out
    res = client.patch(f"/api/reservations/{rid}/check-in")
    assert res.status_code == 422
    assert res.get_json()["error"] == "La reserva ya venció"


def test_rn4_documento_de_huesped_unico(client, guest):
    res = client.post("/api/guests", json={"full_name": "Otra", "email": "otra@example.com", "document": " 123 "})
    assert res.status_code == 409
    assert "documento" in res.get_json()["error"]


def test_rn5_limites_de_estadia_y_anticipacion(reserve):
    assert reserve(1, 32).status_code == 422      # 31 noches
    assert reserve(366, 367).status_code == 422   # 366 días de anticipación
    assert reserve(1, 31).status_code == 201      # 30 noches: límite permitido
