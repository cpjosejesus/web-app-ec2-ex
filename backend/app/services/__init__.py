class ServiceError(Exception):
    """Error de negocio o de validación: el controlador lo traduce a {"error": message} con su código HTTP."""

    def __init__(self, message, status=422):
        super().__init__(message)
        self.message = message
        self.status = status
