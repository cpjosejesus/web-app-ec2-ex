from flask import Blueprint, jsonify, request

from ..services import guests as guest_service
from ..views.guest_view import guest_to_dict, guests_to_list

guest_bp = Blueprint("guests", __name__, url_prefix="/api/guests")


@guest_bp.get("")
def list_guests():
    guests = guest_service.list_guests()
    return jsonify(guests_to_list(guests))


@guest_bp.get("/<int:guest_id>")
def get_guest(guest_id):
    guest = guest_service.get_guest(guest_id)
    return jsonify(guest_to_dict(guest))


@guest_bp.post("")
def create_guest():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        data = {}

    guest = guest_service.create_guest(data)
    return jsonify(guest_to_dict(guest)), 201


@guest_bp.delete("/<int:guest_id>")
def delete_guest(guest_id):
    guest_service.delete_guest(guest_id)
    return "", 204
