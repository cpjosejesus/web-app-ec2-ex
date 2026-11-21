from zoneinfo import ZoneInfo

from flask import Flask
from flask_cors import CORS

from .api import api_bp
from .api.guest_api import guest_bp
from .api.reservation_api import reservation_bp
from .api.room_api import room_bp
from .api.error_handlers import register_error_handlers
from .config import Config
from .models import db
from .seed import seed


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)

    # Detecta una zona mal configurada antes de recibir reservas.
    ZoneInfo(app.config["HOTEL_TIMEZONE"])

    CORS(app)
    db.init_app(app)

    app.register_blueprint(api_bp)
    app.register_blueprint(room_bp)
    app.register_blueprint(guest_bp)
    app.register_blueprint(reservation_bp)
    register_error_handlers(app)

    with app.app_context():
        db.create_all()
        if app.config["SEED"]:
            seed()

    return app
