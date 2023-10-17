class InvalidMethodUse(Exception):
    def __init__(self, reason):
        super().__init__(reason)


class CommandNotFound(Exception):
    def __init__(self, command):
        super().__init__(f"Command with name {command} could not be found")


class ComponentNotFound(Exception):
    def __init__(self, component):
        super().__init__(f"No listener for components with name {component} exists")


class AutocompleteNotFound(Exception):
    def __init__(self, command_name):
        super().__init__(
            f"No listener for autocomplete for command {command_name} exists"
        )


class HTTPRequestError(Exception):
    def __init__(self, status_code, error_message):
        super().__init__(
            f"HTTP request returned with status {status_code}: {error_message}"
        )
