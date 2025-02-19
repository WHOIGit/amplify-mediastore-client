from .api_response import ApiResponse

class BadRequestException(Exception):
    def __init__(self, response: ApiResponse):
        super().__init__()
        self.response = response

class RetryableError(Exception):
    """Raised when the error is transient and could possibly work again if it was retried by the client for a fixed number of times"""
    pass

class NonRetryableError(Exception):
    """Raised when the DOI should not be retried and go straight to the DLQ"""
    pass

class ClientError(Exception):
    """Raised to indicate Client side Error"""
    def __init__(self, response: ApiResponse):
        super().__init__()
        self.response = response

class ServerError(Exception):
    """Raised to indicate Sever side Error"""
    def __init__(self, response: ApiResponse):
        super().__init__()
        self.response = response

class LocalError(Exception):
    """Raised to indicate Local Client code Error"""
    def __init__(self, response: ApiResponse):
        super().__init__()
        self.response = response