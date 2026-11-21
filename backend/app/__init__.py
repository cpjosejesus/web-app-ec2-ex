from flask import Flask
from flask_cors import CORS

from .api import create_api
from .api.error_handlers import register_error_handlers
from .config import Config
from .models import db
from .repositories.guests import GuestRepository
from .repositories.reservations import ReservationRepository
from .repositories.rooms import RoomRepository
from .seed import seed
from .services.guests import GuestService
from .services.reservations import ReservationService
from .services.rooms import RoomService


def create_app(overrides=None):
    app = Flask(__name__)
    app.config.from_object(Config)
    if overrides:
        app.config.update(overrides)

    CORS(app)
    db.init_app(app)

    room_service = RoomService(RoomRepository())
    guest_service = GuestService(GuestRepository())
    reservation_service = ReservationService(
        ReservationRepository(), room_service, guest_service
    )
    app.register_blueprint(create_api(room_service, guest_service, reservation_service))
    register_error_handlers(app)

    with app.app_context():
        db.create_all()
        if app.config["SEED"]:
            seed()

    return app