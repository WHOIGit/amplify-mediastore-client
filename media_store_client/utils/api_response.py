from typing import Dict, Optional

class ApiResponse:
    def __init__(self, status_code: int, response: Optional[Dict] = None, error_message: Optional[str] = None):
        self.status_code = status_code
        self.response = response
        self.error_message = error_message

    def __str__(self) -> str:
        response = f'Status code: {self.status_code}'
        if self.response:
            response += f'\nResponse: {self.response}'
        if self.error_message:
            response += f'\nError message: {self.error_message}'
        return response