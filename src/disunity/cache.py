from . import identifiers
from typing import Dict

class ApplicationCache:
    def __init__(self):
        self.commands: Dict[str, Dict[str, Dict[str, identifiers.DisunityCommand]]] = {'2': {}}
        self.components: Dict[str, identifiers.DisunityComponent] = dict()

    def cache_command(self, command_identifier):
        self.commands[str(command_identifier.type)][command_identifier.name] = command_identifier

    def cache_component(self, component_identifier):
        self.components[str(component_identifier.name)] = component_identifier
