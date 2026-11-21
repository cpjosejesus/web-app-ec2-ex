from flask import jsonify

from ..services.errors import BusinessRuleError, ConflictError, NotFoundError, ValidationError


def register_error_handlers(app):
    @app.errorhandler(BusinessRuleError)
    def handle_business_rule(error):
        return jsonify({"error": str(error)}), 422

    @app.errorhandler(ValidationError)
    def handle_validation(error):
        return jsonify({"error": str(error)}), 400

    @app.errorhandler(NotFoundError)
    def handle_not_found(error):
        return jsonify({"error": str(error)}), 404

    @app.errorhandler(ConflictError)
    def handle_conflict(error):
        return jsonify({"error": str(error)}), 409

    @app.errorhandler(404)
    def handle_missing_route(_error):
        return jsonify({"error": "Ruta no encontrada"}), 404

    @app.errorhandler(405)
    def handle_method_not_allowed(_error):
        return jsonify({"error": "Método no permitido"}), 405
