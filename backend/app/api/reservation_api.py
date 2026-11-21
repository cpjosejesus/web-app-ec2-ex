from flask import Blueprint, jsonify, request

from ..services import reservations as reservation_service
from ..views.reservation_view import reservation_to_dict, reservations_to_list

reservation_bp = Blueprint("reservations", __name__, url_prefix="/api/reservations")


@reservation_bp.get("")
def list_reservations():
    status = request.args.get("status")
    guest_id = request.args.get("guest_id", type=int)
    reservations = reservation_service.list_reservations(status, guest_id)
    return jsonify(reservations_to_list(reservations))


@reservation_bp.get("/<int:reservation_id>")
def get_reservation(reservation_id):
    reservation = reservation_service.get_reservation(reservation_id)
    return jsonify(reservation_to_dict(reservation))


@reservation_bp.post("")
def create_reservation():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        data = {}

    reservation = reservation_service.create_reservation(data)
    return jsonify(reservation_to_dict(reservation)), 201


@reservation_bp.patch("/<int:reservation_id>/cancel")
def cancel_reservation(reservation_id):
    reservation = reservation_service.cancel_reservation(reservation_id)
    return jsonify(reservation_to_dict(reservation))


@reservation_bp.patch("/<int:reservation_id>/check-in")
def check_in_reservation(reservation_id):
    reservation = reservation_service.check_in_reservation(reservation_id)
    return jsonify(reservation_to_dict(reservation))


@reservation_bp.patch("/<int:reservation_id>/check-out")
def check_out_reservation(reservation_id):
    reservation = reservation_service.check_out_reservation(reservation_id)
    return jsonify(reservation_to_dict(reservation))
