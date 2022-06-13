from __future__ import annotations
from re import I
from typing import Optional
from .identifiers import Command, Component, TopLevelSubCommand

import inspect


class Package:
    def __init__(self):
        self.commands = []

    @classmethod
    def command(self, name: str, _type: int, requires_ack: bool = False, requires_ephemeral: bool = False):
        def decorator(coroutine):
            actual = coroutine
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            
            if not inspect.iscoroutinefunction(actual):
                raise TypeError("Command methods must be coroutine")

            actual.__command__ = True
            actual.__component__ = False
            actual.__sub_command__ = False
            actual.__data__ = (name, _type, requires_ack, requires_ephemeral)
            return actual
        return decorator

    @classmethod
    def component(self, name: str, requires_ack: bool = False, requires_ephemeral: bool = False, timeout: float = 0.0):
        def decorator(coroutine):
            actual = coroutine
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            
            if not inspect.iscoroutinefunction(actual):
                raise TypeError("Component methods must be coroutine")
            
            actual.__command__ = False
            actual.__component__ = True
            actual.__sub_command__ = False
            actual.__data__ = (name, requires_ack, requires_ephemeral, timeout)
            return actual
        return decorator

    @classmethod
    def sub(self, name: str, sub_commands: list[str] | str, group: Optional[str] = None, requires_ack: bool = False, requires_ephemeral: bool = False):
        def decorator(coroutine):
            actual = coroutine
            if isinstance(actual, staticmethod):
                actual = actual.__func__
            
            if not inspect.iscoroutinefunction(actual):
                raise TypeError("Sub command methods must be coroutine")
            
            actual.__command__ = False
            actual.__component__ = False
            actual.__sub_command__ = True
            actual.__data__ = (name, sub_commands, group)
            
            return actual
        return decorator

    def _open(self):
        to_return = []
        for m in [attr[1] for attr in inspect.getmembers(self, inspect.iscoroutinefunction) if not attr[0].startswith('__') and not attr[0].endswith('__')]:
            if m.__command__:
                container = Command(m.__data__[0], m.__data__[1], m, m.__data__[2], m.__data__[3])
                to_return.append(container)
            
            elif m.__sub_command__:
                container = TopLevelSubCommand(m.__data__[0], m, m.__data__[1], m.__data__[2])
                to_return.append(container)
            
            elif m.__component__:
                container = Component(m.__data__[0], m, m.__data__[1], m.__data__[2], m.__data__[3])
                to_return.append(container)


        return to_return