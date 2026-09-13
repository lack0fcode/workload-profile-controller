class BackendError(Exception):
    """Base exception for backend failures."""


class ResourceNotFoundError(BackendError):
    """Raised when a resource cannot be resolved."""


class ResourceAmbiguousError(BackendError):
    """Raised when a resource resolves to multiple infrastructure resources."""


class BackendUnavailableError(BackendError):
    """Raised when the backend cannot be reached or used."""


class InvalidResourceStateError(BackendError):
    """Raised when a resource is in an invalid state for an operation."""


class TaskTimeoutError(Exception):
    """Raised when a backend task does not finish before the timeout."""


class TaskFailedError(Exception):
    """Raised when a backend task finishes unsuccessfully."""