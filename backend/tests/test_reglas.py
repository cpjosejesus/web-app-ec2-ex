"""Pruebas de las reglas de negocio RN1 a RN5 (ver REGLAS.md).

Usan las fixtures de conftest.py:
- client: cliente de pruebas de Flask (app.test_client()).
- room: habitación 101, tipo double, capacidad 2, Bs 300 por noche.
- guest: huésped Ana Rojas.
"""
from datetime import date, timedelta


def dia(offset):
    """Fecha relativa a hoy en formato AAAA-MM-DD (offset en días)."""
    return (date.today() + timedelta(days=offset)).isoformat()


def reservar(client, room, guest, desde, hasta, personas=1):
    """Crea una reserva entre los días `desde` y `hasta` (relativos a hoy)."""
    return client.post("/api/reservations", json={
        "room_id": room["id"],
        "guest_id": guest["id"],
        "check_in": dia(desde),
        "check_out": dia(hasta),
        "guests_count": personas,
    })


def assert_regla_incumplida(res):
    """Una regla incumplida responde 422 con un mensaje en "error"."""
    assert res.status_code == 422
    body = res.get_json()
    assert "error" in body
    assert body["error"].strip() != ""


def cantidad_reservas(client):
    return len(client.get("/api/reservations").get_json())


# RN1 · Sin doble reserva

def test_rn1_rechaza_reserva_superpuesta(client, room, guest):
    assert reservar(client, room, guest, 5, 8).status_code == 201

    res = reservar(client, room, guest, 6, 9)

    assert_regla_incumplida(res)
    assert cantidad_reservas(client) == 1


def test_rn1_rechaza_reserva_contenida_en_otra(client, room, guest):
    assert reservar(client, room, guest, 5, 10).status_code == 201

    assert_regla_incumplida(reservar(client, room, guest, 6, 7))


def test_rn1_permite_ingresar_el_dia_que_sale_la_otra(client, room, guest):
    assert reservar(client, room, guest, 5, 8).status_code == 201

    res = reservar(client, room, guest, 8, 10)

    assert res.status_code == 201


def test_rn1_ignora_reservas_canceladas(client, room, guest):
    primera = reservar(client, room, guest, 5, 8).get_json()
    client.patch(f"/api/reservations/{primera['id']}/cancel")

    res = reservar(client, room, guest, 5, 8)

    assert res.status_code == 201


# RN2 · Fechas coherentes

def test_rn2_rechaza_salida_antes_del_ingreso(client, room, guest):
    res = reservar(client, room, guest, 5, 3)

    assert_regla_incumplida(res)
    assert cantidad_reservas(client) == 0


def test_rn2_rechaza_salida_el_mismo_dia_del_ingreso(client, room, guest):
    assert_regla_incumplida(reservar(client, room, guest, 5, 5))


# RN3 · Sin reservas en el pasado

def test_rn3_rechaza_ingreso_en_el_pasado(client, room, guest):
    res = reservar(client, room, guest, -1, 2)

    assert_regla_incumplida(res)
    assert cantidad_reservas(client) == 0


def test_rn3_permite_ingreso_hoy(client, room, guest):
    assert reservar(client, room, guest, 0, 1).status_code == 201


# RN4 · Capacidad de la habitación

def test_rn4_rechaza_mas_personas_que_la_capacidad(client, room, guest):
    res = reservar(client, room, guest, 5, 6, personas=3)

    assert_regla_incumplida(res)
    assert cantidad_reservas(client) == 0


def test_rn4_permite_exactamente_la_capacidad(client, room, guest):
    assert reservar(client, room, guest, 5, 6, personas=2).status_code == 201


# RN5 · Habitación en mantenimiento

def test_rn5_rechaza_habitacion_en_mantenimiento(client, room, guest):
    client.put(f"/api/rooms/{room['id']}", json={"status": "maintenance"})

    res = reservar(client, room, guest, 5, 6)

    assert_regla_incumplida(res)
    assert cantidad_reservas(client) == 0


def test_rn5_permite_reservar_cuando_vuelve_a_estar_disponible(client, room, guest):
    client.put(f"/api/rooms/{room['id']}", json={"status": "maintenance"})
    client.put(f"/api/rooms/{room['id']}", json={"status": "available"})

    assert reservar(client, room, guest, 5, 6).status_code == 201
