from typing import Any


class DomainError(Exception):
    """A business rule failure. Services raise these; the HTTP layer maps them."""

    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFound(DomainError):
    status_code = 404

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, details)
        self.code = code


class RuleViolation(DomainError):
    """The request breaks a rule and would fail regardless of current state."""

    status_code = 422

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, details)
        self.code = code


class Conflict(DomainError):
    """The request is valid but clashes with the current state."""

    status_code = 409

    def __init__(self, code: str, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, details)
        self.code = code
