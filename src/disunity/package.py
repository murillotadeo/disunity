from __future__ import annotations
from .identifiers import (
    TopLevelSubCommand,
    SubOption,
    Component,
    Command 
)

import inspect

class Package:
    def __init__(self):
        self.commands = []
        self.components = []

    @classmethod
    def command(cls, name: str, requires_ack: bool = False, requires_ephemeral: bool = False):
        """
            Declare a command within the application.

            Parameters
            ----------
            name : str
                The command name
            requires_ack : bool
                Does the command need to be acked before the first response.
                Defaulted to False.
            requires_ephemeral : bool
                Only applicable if requires_ack is True. Acks the command 
                using an ephemeral response. Default to False.
        """
        def decorator(coroutine):
            actual = coroutine

            if isinstance(actual, staticmethod):
                actual = actual.__func__

            if not inspect.iscoroutinefunction(actual):
                raise TypeError("Command methods must be coroutine")

            actual.__command__ = True
            actual.__component__ = False
            actual.__subcommand__ = False
            actual.__data__ = (name, requires_ack, requires_ephemeral)

            return actual
        return decorator

    @classmethod
    def component(cls, name: str, requires_ack: bool = False, requires_ephemeral: bool = False, timeout: float = 0.0):
        """"
            Declares a component object within the application

            Parameters
            ----------
            name : str
                The name of the component. Will be gathered in the format
                component_name-<unique tag for this component, preferably
                the interaction id>.
            requires_ack : bool
                Does the interaction need to be acked before the first response
                Default to False.
            requires_ephemeral : bool
                Only applicable if requires_ack is True. Acks the interaction 
                using an ephemeral response.
            timeout : float
                The component timeout. Default to 0.0.
        """
        def decorator(coroutine):
            actual = coroutine
            
            if isinstance(actual, staticmethod):
                actual = actual.__func__

            if not inspect.iscoroutinefunction(actual):
                raise TypeError("Component methods must be coroutine")

            actual.__command__ = False
            actual.__component__ = True
            actual.__subcommand__ = False
            actual.__data__ = (name, requires_ack, requires_ephemeral, timeout)

            return actual
        return decorator

    @classmethod
    def sub(cls, name: str, sub_commands: list[str | SubOption] | str | SubOption, group: None | str = None):
        """
            Declares a sub command within the application

            Parameters
            ----------
            name : str
                The name of the command base.
            sub_commands : list[str | SubOption] | str | SubOption
                The sub command options that this command has.
            group : str | None
                The group that the sub commands belong to. Defaults to None.
        """
        def decorator(coroutine):
            actual = coroutine
            if isinstance(actual, staticmethod):
                actual = actual.__func__

            if not inspect.iscoroutinefunction(actual):
                raise TypeError("Sub command methods must be coroutine")

            actual.__command__ = False
            actual.__component__ = False
            actual.__subcommand__ = True
            actual.__data__ = (name, sub_commands, group)

            return actual
        return decorator

    
    def unpack(self):
        to_return = []

        for meth in [attr[1] for attr in inspect.getmembers(self, inspect.iscoroutinefunction) if not attr[0].startswith('__') and not attr[0].endswith('__')]:
            try:
                d = meth.__data__

                if meth.__command__:
                    to_return.append(Command(d[0], meth, d[1], d[2]))

                elif meth.__component__:
                    to_return.append(Component(d[0], meth, d[1], d[2], d[3]))

                elif meth.__subcommand__:
                    to_return.append(TopLevelSubCommand(d[0], meth, d[1], d[2]))

            except AttributeError:
                continue

        return to_return
