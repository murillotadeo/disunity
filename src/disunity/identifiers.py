from typing import Callable
from datetime import datetime, timezone

class SubOption:
    """
        Represents a sub command option 
        
        Parameters
        ----------
        name : str
            The name of the sub command 
        requires_ack : bool
            Does the command need to be acked (response using followup). Default
            to False
        requires_ephemeral : bool
            Only required if requires_ack is true. Sets the initial ack message 
            to show ephemerally so following responses can be ephemeral.
    """
    def __init__(
        self,
        name: str,
        requires_ack: bool = False,
        requires_ephemeral: bool = False 
    ):
        self.name: str = name
        self.ack: bool = requires_ack
        self.ephemeral: bool = requires_ephemeral

class SubCommand(SubOption):
    def __init__(
        self,
        name: str,
        coroutine: Callable,
        requires_ack: bool = False,
        requires_ephemeral: bool = False 
    ):
        super().__init__(name, requires_ack, requires_ephemeral)
        self.name: str = name
        self.coroutine: Callable = coroutine

    async def __call__(self, context):
        try:
            response = await self.coroutine(context)
            if isinstance(response, dict):
                return response
        except Exception as e:
            context._app.error_handler(e)

class TopLevelSubCommand:
    def __init__(
        self,
        name: str,
        coroutine: Callable,
        sub_commands: list[str] | list[SubCommand] | SubCommand | str = [],
        group: str | None = None 
    ):
        self.name: str = name
        self.coroutine: Callable = coroutine
        self.sub_commands = []
        self.group = group

        if isinstance(sub_commands, str):
            self.sub_commands.append(SubCommand(sub_commands, self.coroutine, False, False))
        elif isinstance(sub_commands, list):
            for sub in sub_commands:
                if isinstance(sub, str):
                    self.sub_commands.append(SubCommand(sub, self.coroutine, False, False))
                elif isinstance(sub, SubOption):
                    self.sub_commands.append(SubCommand(sub.name, self.coroutine, sub.ack, sub.ephemeral))
        elif isinstance(sub_commands, SubOption):
            self.sub_commands.append(SubCommand(sub_commands.name, self.coroutine, sub_commands.ack, sub_commands.ephemeral))

class CacheableSubCommand:
    def __init__(
        self,
        name: str 
    ):
        self.name: str = name
        self.map = {"sub_commands": {}}

    def add(self, incoming: TopLevelSubCommand):
        if incoming.group is not None:
            self.map[str(incoming.group)] = {}
            for sub in incoming.sub_commands:
                self.map[str(incoming.group)][str(sub.name)] = sub
        else:
            for sub in incoming.sub_commands:
                self.map["sub_commands"][str(sub.name)] = sub

        return self

class Component:
    def __init__(
        self,
        name: str,
        coroutine: Callable,
        requires_ack: bool = False,
        requires_ephemeral: bool = False,
        timeout: float = 0.0
    ):
        self.name: str = name
        self.coroutine: Callable = coroutine
        self.ack: bool = requires_ack
        self.ephemeral: bool = requires_ephemeral
        self.timeout: float | None = None if timeout <= 0.0 else timeout 
    
    async def __call__(self, context):
        if isinstance(self.timeout, float):
            if ((datetime.now(timezone.utc) - datetime.fromisoformat(context.raw["message"]["timestamp"])).total_seconds() > self.timeout):
                if not self.ack:
                    return {"type": 4, "data": {"content": "This component has timed out.", "flags": 64}}

        try:
            response = await self.coroutine(context)
            if isinstance(response, dict):
                return response
        except Exception as e:
            context._app.error_handler(e)

class Command:
    def __init__(
        self,
        name: str,
        coroutine: Callable,
        requires_ack: bool = False,
        requires_ephemeral: bool = False 
    ):
        self.name: str = name
        self.command_type: int = 2
        self.coroutine: Callable = coroutine
        self.ack: bool = requires_ack
        self.ephemeral: bool = requires_ephemeral

    async def __call__(self, context):
        try:
            response = await self.coroutine(context)
            if isinstance(response, dict):
                return response
        except Exception as e:
            context._app.error_handler(e)
