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
    def command(self, name: str, _type: int, requires_ephemeral: bool = False, requires_ack: bool = True):
        def decorator(coroutine):
            actual = coroutine
            if isinstance(actual, staticmethod):
                actual = actual.__func__

            if not inspect.iscoroutinefunction(actual):
                raise TypeError("Command functions must be coroutine")

            actual.__command__ = True
            actual.__data__ = (name, _type, requires_ephemeral, requires_ack)
            return actual
        return decorator

    @classmethod
    def component(self, name: str, requires_ack: bool = False, requires_ephemeral: bool = False, timeout: float = 0.0):
        def decorator(coroutine):
            actual = coroutine
            if isinstance(actual, staticmethod):
                actual = actual.__func__

            if not inspect.iscoroutinefunction(actual):
                raise TypeError("Component functions must be coroutine")
            
            actual.__component__ = True
            actual.__command__ = False
            actual.__data__ = (name, requires_ack, requires_ephemeral, timeout)
            return actual
        return decorator

    def _open(self):
        contents = []
        for attribute in [attr[1] for attr in inspect.getmembers(self, inspect.iscoroutinefunction) if not attr[0].startswith('__') and not attr[0].endswith('__')]:
            try:
                if attribute.__command__:
                    content = identifiers.DisunityCommand(attribute.__data__[0], attribute.__data__[1], attribute, attribute.__data__[3], attribute.__data__[2])
                elif attribute.__component__:
                    content = identifiers.DisunityComponent(attribute.__data__[0], attribute, attribute.__data__[1], attribute.__data__[2], attribute.__data__[3])
                contents.append(content)
            except AttributeError:
                pass

        return contents
