# Capa de rutas: recibe la petición HTTP, llama al servicio y serializa la respuesta (JSON).
from flask import Blueprint, jsonify, request

from ..services.guest_service import GuestService
from ..views.guest_view import guest_to_dict, guests_to_list

guest_bp = Blueprint("guests", __name__, url_prefix="/api/guests")
guest_service = GuestService()


@guest_bp.get("")
def list_guests():
    return jsonify(guests_to_list(guest_service.list_guests()))


@guest_bp.get("/<int:guest_id>")
def get_guest(guest_id):
    return jsonify(guest_to_dict(guest_service.get_guest(guest_id)))


@guest_bp.post("")
def create_guest():
    guest = guest_service.create_guest(request.get_json(silent=True) or {})
    return jsonify(guest_to_dict(guest)), 201


@guest_bp.delete("/<int:guest_id>")
def delete_guest(guest_id):
    guest_service.delete_guest(guest_id)
    return "", 204
