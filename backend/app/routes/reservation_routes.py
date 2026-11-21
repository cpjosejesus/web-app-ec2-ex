# Capa de rutas: recibe la petición HTTP, llama al servicio y serializa la respuesta (JSON).
from flask import Blueprint, jsonify, request

from ..services.reservation_service import ReservationService
from ..views.reservation_view import reservation_to_dict, reservations_to_list

reservation_bp = Blueprint("reservations", __name__, url_prefix="/api/reservations")
reservation_service = ReservationService()


@reservation_bp.get("")
def list_reservations():
    reservations = reservation_service.list_reservations(
        request.args.get("status"), request.args.get("guest_id", type=int))
    return jsonify(reservations_to_list(reservations))


@reservation_bp.get("/<int:reservation_id>")
def get_reservation(reservation_id):
    return jsonify(reservation_to_dict(reservation_service.get_reservation(reservation_id)))


@reservation_bp.post("")
def create_reservation():
    reservation = reservation_service.create_reservation(request.get_json(silent=True) or {})
    return jsonify(reservation_to_dict(reservation)), 201


@reservation_bp.patch("/<int:reservation_id>/cancel")
def cancel_reservation(reservation_id):
    return jsonify(reservation_to_dict(reservation_service.cancel_reservation(reservation_id)))


@reservation_bp.patch("/<int:reservation_id>/check-in")
def check_in_reservation(reservation_id):
    return jsonify(reservation_to_dict(reservation_service.check_in_reservation(reservation_id)))


@reservation_bp.patch("/<int:reservation_id>/check-out")
def check_out_reservation(reservation_id):
    return jsonify(reservation_to_dict(reservation_service.check_out_reservation(reservation_id)))
