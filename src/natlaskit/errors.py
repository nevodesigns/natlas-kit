"""Exception types for natlas-kit."""


class NatlasError(Exception):
    """Base error for everything in natlas-kit."""


class BackendError(NatlasError):
    """Raised when an N-ATLaS backend (endpoint) returns an error or is unreachable."""


class SchemaError(NatlasError):
    """Raised when a structured-extraction result cannot be parsed or validated."""
