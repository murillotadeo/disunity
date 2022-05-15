from __future__ import annotations
from typing import Callable, Any, TypeVar
from . import identifiers

import inspect

PackageT = TypeVar('PackageT', bound='Package')
CoroT = TypeVar('CoroT', bound=Callable[..., Any])

class Package:
    def __init__(self):
        self.commands = []
    
    @classmethod
    def command(self, name: str, _type: int, requires_ephemeral: bool = False):
        def decorator(coroutine):
            actual = coroutine
            if isinstance(actual, staticmethod):
                actual = actual.__func__

            if not inspect.iscoroutinefunction(actual):
                raise TypeError("Command functions must be coroutine")

            actual.__ext_command__ = True
            actual.__command_data__ = (name, _type, requires_ephemeral)
            return actual
        return decorator

    def _open(self):
        contents = []
        for attribute in [attr[1] for attr in inspect.getmembers(self, inspect.iscoroutinefunction) if not attr[0].startswith('__') and not attr[0].endswith('__')]:
            try:
                content = identifiers.Command(attribute.__command_data__[0], attribute, attribute.__command_data__[1], attribute.__command_data__[2])
                contents.append(content)
            except AttributeError:
                pass

        return contents
