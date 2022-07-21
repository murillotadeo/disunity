class InvalidMethodUse(Exception):
    def __init__(self, reason):
        super().__init__(reason)

class CommandNotFound(Exception):
    def __init__(self, command):
        super().__init__("Command with name {} could not be found".format(command))

class ComponentNotFound(Exception):
    def __init__(self, component):
        super().__init__("No listener for components with name {} exist".format(component))

class HTTPRequestError(Exception):
    def __init__(self, status_code, error_message):
        super().__init__("HTTP request returned with status {}: {}".format(status_code, error_message))
