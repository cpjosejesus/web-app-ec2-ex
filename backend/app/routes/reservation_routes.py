from flask import Blueprint, jsonify, request

from ..services.reservation_service import (
    cancel_reservation,
    check_in_reservation,
    check_out_reservation,
    create_reservation,
    get_reservation,
    list_reservations,
)
from ..views.reservation_view import reservation_to_dict, reservations_to_list

reservation_bp = Blueprint("reservations", __name__, url_prefix="/api/reservations")


@reservation_bp.get("")
def list_reservations_route():
    status = request.args.get("status")
    guest_id = request.args.get("guest_id", type=int)
    reservations = list_reservations(status=status, guest_id=guest_id)
    return jsonify(reservations_to_list(reservations))


@reservation_bp.get("/<int:reservation_id>")
def get_reservation_route(reservation_id):
    result = get_reservation(reservation_id)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return jsonify(reservation_to_dict(result))


@reservation_bp.post("")
def create_reservation_route():
    data = request.get_json(silent=True) or {}
    result = create_reservation(data)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return jsonify(reservation_to_dict(result)), 201


@reservation_bp.patch("/<int:reservation_id>/cancel")
def cancel_reservation_route(reservation_id):
    result = cancel_reservation(reservation_id)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return jsonify(reservation_to_dict(result))


@reservation_bp.patch("/<int:reservation_id>/check-in")
def check_in_reservation_route(reservation_id):
    result = check_in_reservation(reservation_id)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return jsonify(reservation_to_dict(result))


@reservation_bp.patch("/<int:reservation_id>/check-out")
def check_out_reservation_route(reservation_id):
    result = check_out_reservation(reservation_id)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return jsonify(reservation_to_dict(result))