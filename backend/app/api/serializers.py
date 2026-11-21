def room_to_dict(room):
    return {
        "id": room.id,
        "number": room.number,
        "type": room.type,
        "price_per_night": room.price_per_night,
        "capacity": room.capacity,
        "status": room.status,
    }


def rooms_to_list(rooms):
    return [room_to_dict(room) for room in rooms]


def guest_to_dict(guest):
    return {
        "id": guest.id,
        "full_name": guest.full_name,
        "email": guest.email,
        "document": guest.document,
    }


def guests_to_list(guests):
    return [guest_to_dict(guest) for guest in guests]


def reservation_to_dict(reservation):
    return {
        "id": reservation.id,
        "room_id": reservation.room_id,
        "room_number": reservation.room.number,
        "guest_id": reservation.guest_id,
        "guest_name": reservation.guest.full_name,
        "check_in": reservation.check_in.isoformat(),
        "check_out": reservation.check_out.isoformat(),
        "nights": (reservation.check_out - reservation.check_in).days,
        "guests_count": reservation.guests_count,
        "status": reservation.status,
        "total_price": round(reservation.total_price, 2),
        "created_at": reservation.created_at.isoformat(timespec="seconds"),
    }


def reservations_to_list(reservations):
    return [reservation_to_dict(reservation) for reservation in reservations]
