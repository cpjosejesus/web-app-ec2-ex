from ..models import db


class BaseRepository:
    """Operaciones comunes de escritura. Cada repositorio indica su modelo."""

    model = None

    def get(self, entity_id):
        return db.session.get(self.model, entity_id)

    def save(self, entity):
        db.session.add(entity)
        db.session.commit()
        return entity

    def commit(self):
        db.session.commit()

    def delete(self, entity):
        db.session.delete(entity)
        db.session.commit()
