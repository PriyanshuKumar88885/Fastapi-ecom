"""
Custom exception classes for the application.

These are used to provide consistent error handling across routers.
"""


class BaseAPIException(Exception):
    """Base exception for all API errors."""

    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class ResourceNotFoundError(BaseAPIException):
    """Raised when a resource (tenant, user, product, order) is not found."""

    def __init__(self, resource: str, identifier: str = None):
        message = f"{resource} not found"
        if identifier:
            message += f": {identifier}"
        super().__init__(message, status_code=404)


class ResourceAlreadyExistsError(BaseAPIException):
    """Raised when attempting to create a duplicate resource."""

    def __init__(self, resource: str, field: str = None):
        message = f"{resource} already exists"
        if field:
            message += f" (field: {field})"
        super().__init__(message, status_code=400)


class ValidationError(BaseAPIException):
    """Raised for invalid input data."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)


class InsufficientQuantityError(BaseAPIException):
    """Raised when order quantity exceeds available product quantity."""

    def __init__(self, product_id: int, requested: int, available: int):
        message = f"Insufficient quantity for product {product_id}. Requested: {requested}, Available: {available}"
        super().__init__(message, status_code=400)


class PermissionDeniedError(BaseAPIException):
    """Raised when user lacks required permissions."""

    def __init__(self, message: str = "Permission denied"):
        super().__init__(message, status_code=403)


class UnauthorizedError(BaseAPIException):
    """Raised when user is not authenticated."""

    def __init__(self, message: str = "Not authenticated"):
        super().__init__(message, status_code=401)


class InvalidTokenError(BaseAPIException):
    """Raised when authentication token is invalid or expired."""

    def __init__(self, reason: str = "Invalid or expired token"):
        super().__init__(reason, status_code=401)


class AlreadyFavouritedError(BaseAPIException):
    """Raised when attempting to favourite already favourited product."""

    def __init__(self):
        super().__init__("Product already favourited", status_code=400)


class NotFavouritedError(BaseAPIException):
    """Raised when attempting to unfavourite non-favourited product."""

    def __init__(self):
        super().__init__("Product not favourited", status_code=400)


class InvalidOperationError(BaseAPIException):
    """Raised when an operation is invalid or cannot be performed."""

    def __init__(self, message: str):
        super().__init__(message, status_code=400)
