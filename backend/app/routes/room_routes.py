from flask import Blueprint, jsonify, request

from ..services import RoomService
from ..views.room_view import room_to_dict, rooms_to_list

room_bp = Blueprint("rooms", __name__, url_prefix="/api/rooms")
service = RoomService()


@room_bp.get("")
def list_rooms():
    rooms = service.list(status=request.args.get("status"))
    return jsonify(rooms_to_list(rooms))


@room_bp.get("/<int:room_id>")
def get_room(room_id):
    return jsonify(room_to_dict(service.get(room_id)))


@room_bp.post("")
def create_room():
    room = service.create(request.get_json(silent=True) or {})
    return jsonify(room_to_dict(room)), 201


@room_bp.put("/<int:room_id>")
def update_room(room_id):
    room = service.update(room_id, request.get_json(silent=True) or {})
    return jsonify(room_to_dict(room))


@room_bp.delete("/<int:room_id>")
def delete_room(room_id):
    service.delete(room_id)
    return "", 204
