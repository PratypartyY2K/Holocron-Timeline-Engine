class DomainError(Exception):
    """Base class for domain and application errors."""


class EntityNotFoundError(DomainError):
    pass


class DuplicateEntityError(DomainError):
    pass


class ValidationError(DomainError):
    pass


class ChronologyError(ValidationError):
    pass


class UnsupportedRelationshipError(ValidationError):
    pass

