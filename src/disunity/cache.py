class ApplicationCache:
    def __init__(self):
        self.commands = {"2": {}}
        self.components = dict()

    def cache_command(self, command_identifier):
        self.commands[command_identifier.type] = command_identifier

    def cache_component(self, component_identifier):
        self.components[component_identifier.custom_id] = component_identifier
