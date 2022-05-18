class ComponentNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)

class CommandNotFound(Exception):
    def __init__(self, message):
        super().__init__(message)

class HTTPRequestError(Exception):
    def __init__(self, http_status_code, error):
        super().__init__(f"Request returned with status: {http_status_code}. Request body: {error}")

class ComponentInvokeError(Exception):
    def __init__(self, message):
        super().__init__(message)

class CommandInvokeError(Exception):
    def __init__(self, message):
        super().__init__(message)

class InvalidMethodUse(Exception):
    def __init__(self, message):
        super().__init__(message)
