"""Único lugar donde los errores de la aplicación se traducen a HTTP."""
from flask import jsonify

from .services.exceptions import (
    AppError,
    BusinessRuleError,
    ConflictError,
    NotFoundError,
    ValidationError,
)

STATUS_CODES = {
    ValidationError: 400,
    NotFoundError: 404,
    ConflictError: 409,
    BusinessRuleError: 422,
}


def register_error_handlers(app):
    @app.errorhandler(AppError)
    def handle_app_error(error):
        status = STATUS_CODES.get(type(error), 400)
        return jsonify({"error": error.message}), status

    @app.errorhandler(404)
    def not_found(_error):
        return jsonify({"error": "Ruta no encontrada"}), 404

    @app.errorhandler(405)
    def method_not_allowed(_error):
        return jsonify({"error": "Método no permitido"}), 405
