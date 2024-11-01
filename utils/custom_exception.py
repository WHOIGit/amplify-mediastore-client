class APIException(Exception):
    def __init__(self):
        # todo
        print()

class BadRequestException(Exception):
    pass

class RetryableError(Exception):
    """Raised when the error is transient and could possibly work again if it was retried by the client for a fixed number of times"""
    pass

class NonRetryableError(Exception):
    """Raised when the DOI should not be retried and go straight to the DLQ"""
    pass

class ClientError(Exception):
    """Raised to indicate Client side Error"""
    pass