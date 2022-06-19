from .identifiers import Command, Component, TopLevelSubCommand, CacheableSubCommand

class ApplicationCache:
    def __init__(self):
        self.commands = {"2": {}}
        self.components = dict()

    def cache_item(self, item):
        if isinstance(item, TopLevelSubCommand):
            if str(item.name) in self.commands['2']:
                self.commands['2'][str(item.name)]._map(item)
            else:
                cacheable = CacheableSubCommand(str(item.name))
                cacheable._map(item)

                self.commands['2'][str(item.name)] = cacheable

        elif isinstance(item, Command):
            self.commands['2'][str(item.name)] = item
        elif isinstance(item, Component):
            self.components[str(item.name)] = item
        else:
            raise TypeError
