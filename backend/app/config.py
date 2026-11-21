import os


class Config:
    HOTEL_TIMEZONE = os.getenv("HOTEL_TIMEZONE", "America/La_Paz")
    SQLALCHEMY_DATABASE_URI = os.getenv("DATABASE_URL", "sqlite:///hotel.db")
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JSON_SORT_KEYS = False
    SEED = os.getenv("SEED", "1") == "1"
