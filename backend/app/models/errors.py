class SkipQError(Exception):
    """Base for refusals the API turns into a 4xx carrying a message the
    persona who caused it can act on (TMA Q3d)."""

    status_code = 400

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code


class RuleViolation(SkipQError):
    """A business rule refused the action in the state it was attempted."""
    status_code = 409


class NotPermitted(SkipQError):
    """The caller's role or scope does not allow this action."""
    status_code = 403


class NotFound(SkipQError):
    status_code = 404
