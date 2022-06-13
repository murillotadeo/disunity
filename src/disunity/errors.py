class ComponentNotFound(Exception):
    def __init__(self, component):
        super().__init__(f"{component} was not found.")

class CommandNotFound(Exception):
    def __init__(self, command):
        super().__init__(f"{command} was not found.")

class HTTPRequestError(Exception):
    def __init__(self, status_code, error):
        super().__init__(f"Request returned with status: {status_code}. Request body: {error}")

class InvocationError(Exception):
    def __init__(self, coroutine_name, error):
        super().__init__(f"Error when running {coroutine_name}: {error}")

class InvalidMethodUse(Exception):
    def __init__(self, message):
        super().__init__(message)

class NotImplementedError(Exception):
    def __init__(self, message):
        super().__init__(message)
