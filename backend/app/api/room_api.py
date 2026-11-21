from flask import Blueprint, jsonify, request

from ..services import rooms as room_service
from .serializers import room_to_dict, rooms_to_list

room_bp = Blueprint("rooms", __name__, url_prefix="/api/rooms")


@room_bp.get("")
def list_rooms():
    status = request.args.get("status")
    rooms = room_service.list_rooms(status)
    return jsonify(rooms_to_list(rooms))


@room_bp.get("/<int:room_id>")
def get_room(room_id):
    room = room_service.get_room(room_id)
    return jsonify(room_to_dict(room))


@room_bp.post("")
def create_room():
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        data = {}

    room = room_service.create_room(data)
    return jsonify(room_to_dict(room)), 201


@room_bp.put("/<int:room_id>")
def update_room(room_id):
    data = request.get_json(silent=True) or {}
    if not isinstance(data, dict):
        data = {}

    room = room_service.update_room(room_id, data)
    return jsonify(room_to_dict(room))


@room_bp.delete("/<int:room_id>")
def delete_room(room_id):
    room_service.delete_room(room_id)
    return "", 204
