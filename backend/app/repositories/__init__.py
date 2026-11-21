"""Persistencia del sistema de recepción."""

from sqlalchemy.exc import SQLAlchemyError

from ..models import db


def commit():
    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        raise
