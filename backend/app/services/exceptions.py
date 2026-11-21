"""Errores propios de la aplicación.

Son excepciones de Python puras: los servicios las lanzan sin saber nada de HTTP.
La traducción a código HTTP + JSON se hace en un solo lugar: app/errors.py.
"""


class AppError(Exception):
    """Base de todos los errores de la aplicación."""

    def __init__(self, message):
        super().__init__(message)
        self.message = message


class ValidationError(AppError):
    """Los datos de entrada están incompletos o tienen un formato inválido."""


class NotFoundError(AppError):
    """El recurso pedido no existe."""


class ConflictError(AppError):
    """La operación choca con datos que ya existen (duplicados, dependencias)."""


class BusinessRuleError(AppError):
    """Se incumple una regla de negocio (ver REGLAS.md)."""
