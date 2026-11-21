class BusinessRuleError(Exception):
    """Error previsto en un caso de uso."""


class ValidationError(BusinessRuleError):
    """Los datos de entrada no son válidos."""


class NotFoundError(BusinessRuleError):
    """La entidad solicitada no existe."""


class ConflictError(BusinessRuleError):
    """La operación entra en conflicto con los datos existentes."""