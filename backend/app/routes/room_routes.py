from flask import Blueprint, jsonify, request

from ..services.room_service import (
    create_room,
    delete_room,
    get_room,
    list_rooms,
    update_room,
)
from ..views.room_view import room_to_dict, rooms_to_list

room_bp = Blueprint("rooms", __name__, url_prefix="/api/rooms")


@room_bp.get("")
def list_rooms_route():
    status = request.args.get("status")
    rooms = list_rooms(status=status)
    return jsonify(rooms_to_list(rooms))


@room_bp.get("/<int:room_id>")
def get_room_route(room_id):
    result = get_room(room_id)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return jsonify(room_to_dict(result))


@room_bp.post("")
def create_room_route():
    data = request.get_json(silent=True) or {}
    result = create_room(data)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return jsonify(room_to_dict(result)), 201


@room_bp.put("/<int:room_id>")
def update_room_route(room_id):
    data = request.get_json(silent=True) or {}
    result = update_room(room_id, data)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return jsonify(room_to_dict(result))


@room_bp.delete("/<int:room_id>")
def delete_room_route(room_id):
    result = delete_room(room_id)
    if isinstance(result, dict) and "error" in result:
        return jsonify({"error": result["error"]}), result["status"]
    return "", 204