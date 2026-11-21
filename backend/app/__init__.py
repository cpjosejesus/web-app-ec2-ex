from flask import Flask, jsonify
from flask_cors import CORS

from .config import Config
from .errors import register_error_handlers
from .models import db
from .routes.guest_routes import guest_bp
from .routes.reservation_routes import reservation_bp
from .routes.room_routes import room_bp
from .seed import seed


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)

    CORS(app)
    db.init_app(app)

    app.register_blueprint(room_bp)
    app.register_blueprint(guest_bp)
    app.register_blueprint(reservation_bp)
    register_error_handlers(app)

    @app.get("/api/health")
    def health():
        return jsonify({"status": "ok"})

    with app.app_context():
        db.create_all()
        if app.config["SEED"]:
            seed()

    return app
