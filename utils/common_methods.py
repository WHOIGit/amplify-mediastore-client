class ApiResponse:
    def __init__(self, status_code: int, response: Optional[Dict] = None, exception: Optional[Exception] = None):
        self.status_code = status_code
        self.response = None
        self.exception = None
        if response:
            self.response = response
        if exception:
            self.exception = exception

    def __str__(self) -> str:
        attrs = [f"Status code: {self.status_code}"]
        if self.response:
            attrs.append(f"Response: {self.response}")
        elif self.exception:
            attrs.append(f"Error: {self.exception}")
        return ", ".join(attrs)