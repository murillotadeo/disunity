from .identifiers import (
    Autocomplete,
    CacheableSubCommand,
    Command,
    Component,
    TopLevelSubCommand,
)


class ApplicationCache:
    def __init__(self):
        self.commands = dict()
        self.components = dict()
        self.autocompletes = dict()

    def add_item(
        self, incoming: TopLevelSubCommand | Command | Component | Autocomplete
    ):
        if isinstance(incoming, TopLevelSubCommand):
            if "2" not in self.commands:
                self.commands["2"] = {}  # Sub commands will always by type 2

            if incoming.name in self.commands["2"]:
                self.commands["2"][str(incoming.name)].add(incoming)
            else:
                cacheable = CacheableSubCommand(str(incoming.name)).add(incoming)
                self.commands["2"][str(incoming.name)] = cacheable

        elif isinstance(incoming, Command):
            if str(incoming.command_type) not in self.commands:
                self.commands[str(incoming.command_type)] = {}
            self.commands[str(incoming.command_type)][incoming.name] = incoming

        elif isinstance(incoming, Component):
            self.components[str(incoming.name)] = incoming

        elif isinstance(incoming, Autocomplete):
            self.autocompletes[str(incoming.command_name)] = incoming

        else:
            raise TypeError
