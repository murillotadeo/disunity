class Warehouse:
    """Storage for all the application's package contents"""

    def __init__(self):
        self.commands = {"2": {}}
        self.components = {}

    def deliver_command(self, command):
        self.commands[str(command.type)][command.name] = command

    def deliver_component(self, component):
        self.components[component.custom_id] = component
