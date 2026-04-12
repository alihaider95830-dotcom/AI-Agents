class StudioException(Exception):
    def __init__(self, message: str, status_code: int) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code


class NotFoundError(StudioException):
    def __init__(self, message: str = "Resource not found") -> None:
        super().__init__(message=message, status_code=404)


class ForbiddenError(StudioException):
    def __init__(self, message: str = "Forbidden") -> None:
        super().__init__(message=message, status_code=403)


class InsufficientCreditsError(StudioException):
    def __init__(self, message: str = "Insufficient credits") -> None:
        super().__init__(message=message, status_code=402)


class JobFailedError(StudioException):
    def __init__(self, message: str = "Job failed") -> None:
        super().__init__(message=message, status_code=500)
