from abc import ABC

from ..models import db


class Repository(ABC):
    model = None  # el repositorio concreto define aquí su modelo

    def __init__(self):
        if self.model is None:
            raise TypeError(f"{type(self).__name__} debe definir el atributo 'model'")

    def get_all(self):
        return self.model.query.all()

    def get_by_id(self, entity_id):
        return db.session.get(self.model, entity_id)

    def create(self, **fields):
        entity = self.model(**fields)
        db.session.add(entity)
        db.session.commit()
        return entity

    def update(self, entity, **fields):
        for name, value in fields.items():
            setattr(entity, name, value)
        db.session.commit()
        return entity

    def delete(self, entity):
        db.session.delete(entity)
        db.session.commit()

    def close_db_session(self):
        db.session.close()
