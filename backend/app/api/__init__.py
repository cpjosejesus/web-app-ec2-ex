from flask import Blueprint, jsonify, request

from ..views.guest_view import guest_to_dict, guests_to_list
from ..views.reservation_view import reservation_to_dict, reservations_to_list
from ..views.room_view import room_to_dict, rooms_to_list


def _json_body():
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def create_api(room_service, guest_service, reservation_service):
    api_bp = Blueprint("api", __name__, url_prefix="/api")

    @api_bp.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @api_bp.get("/rooms")
    def list_rooms():
        return jsonify(rooms_to_list(room_service.list_rooms(request.args.get("status"))))

    @api_bp.get("/rooms/<int:room_id>")
    def get_room(room_id):
        return jsonify(room_to_dict(room_service.get_room(room_id)))

    @api_bp.post("/rooms")
    def create_room():
        room = room_service.create_room(_json_body())
        return jsonify(room_to_dict(room)), 201

    @api_bp.put("/rooms/<int:room_id>")
    def update_room(room_id):
        return jsonify(room_to_dict(room_service.update_room(room_id, _json_body())))

    @api_bp.delete("/rooms/<int:room_id>")
    def delete_room(room_id):
        room_service.delete_room(room_id)
        return "", 204

    @api_bp.get("/guests")
    def list_guests():
        return jsonify(guests_to_list(guest_service.list_guests()))

    @api_bp.get("/guests/<int:guest_id>")
    def get_guest(guest_id):
        return jsonify(guest_to_dict(guest_service.get_guest(guest_id)))

    @api_bp.post("/guests")
    def create_guest():
        guest = guest_service.create_guest(_json_body())
        return jsonify(guest_to_dict(guest)), 201

    @api_bp.delete("/guests/<int:guest_id>")
    def delete_guest(guest_id):
        guest_service.delete_guest(guest_id)
        return "", 204

    @api_bp.get("/reservations")
    def list_reservations():
        status = request.args.get("status")
        guest_id = request.args.get("guest_id", type=int)
        result = reservation_service.list_reservations(status, guest_id)
        return jsonify(reservations_to_list(result))

    @api_bp.get("/reservations/<int:reservation_id>")
    def get_reservation(reservation_id):
        reservation = reservation_service.get_reservation(reservation_id)
        return jsonify(reservation_to_dict(reservation))

    @api_bp.post("/reservations")
    def create_reservation():
        reservation = reservation_service.create_reservation(_json_body())
        return jsonify(reservation_to_dict(reservation)), 201

    @api_bp.patch("/reservations/<int:reservation_id>/cancel")
    def cancel_reservation(reservation_id):
        reservation = reservation_service.cancel_reservation(reservation_id)
        return jsonify(reservation_to_dict(reservation))

    @api_bp.patch("/reservations/<int:reservation_id>/check-in")
    def check_in_reservation(reservation_id):
        reservation = reservation_service.check_in_reservation(reservation_id)
        return jsonify(reservation_to_dict(reservation))

    @api_bp.patch("/reservations/<int:reservation_id>/check-out")
    def check_out_reservation(reservation_id):
        reservation = reservation_service.check_out_reservation(reservation_id)
        return jsonify(reservation_to_dict(reservation))

    return api_bp
