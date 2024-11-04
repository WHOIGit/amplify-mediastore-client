from typing import Dict, Optional

class ApiResponse:
    def __init__(self, status_code: int, response: Optional[Dict] = None, error_message: Optional[str] = None):
        self.status_code = status_code
        self.response = response
        self.error_message = error_message

    def __str__(self) -> str:
        attrs = [f'ApiResponse | Status code: {self.status_code}']
        if hasattr(self, 'response') and self.response:
            attrs.append(f"Response: {self.response}")
        elif hasattr(self, 'error_message') and self.error_message:
            attrs.append(f"Error: {self.error_message}")
        return ", ".join(attrs)