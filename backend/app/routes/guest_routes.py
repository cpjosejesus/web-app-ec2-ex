from flask import Blueprint, jsonify, request

from ..services.guest_service import (
    create_guest,
    delete_guest,
    get_guest,
    list_guests,
)
from ..views.guest_view import guest_to_dict, guests_to_list

guest_bp = Blueprint("guests", __name__, url_prefix="/api/guests")


@guest_bp.get("")
def list_guests_route():
    guests = list_guests()
    return jsonify(guests_to_list(guests))


@guest_bp.get("/<int:guest_id>")
def get_guest_route(guest_id):
    result = get_guest(guest_id)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return jsonify(guest_to_dict(result))


@guest_bp.post("")
def create_guest_route():
    data = request.get_json(silent=True) or {}
    result = create_guest(data)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return jsonify(guest_to_dict(result)), 201


@guest_bp.delete("/<int:guest_id>")
def delete_guest_route(guest_id):
    result = delete_guest(guest_id)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return "", 204