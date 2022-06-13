from typing import Callable
from datetime import datetime, timezone
from .errors import InvocationError
from . import utils


class SubCommand:
    def __init__(
        self,
        name: str,
        coroutine: Callable,

    ):
        self.name = name 
        self.coroutine = coroutine


    async def __call__(self, context):
        try:
            response = await self.coroutine(context)
            if response is not None and type(response) == dict:
                return response
        except Exception as e:
            raise InvocationError(self.coroutine.__qualname__, e)


class TopLevelSubCommand:
    def __init__(
        self,
        name: str,
        coroutine: Callable,
        sub_commands: list[str] | str,
        group_name: str | None,
    ):
        self.name = name
        self.coroutine = coroutine
        self.group_name = group_name
        self.sub_commands: list[str] | str = []
        if isinstance(sub_commands, list):
            for sub in list(sub_commands):
                self.sub_commands.append(SubCommand(sub, self.coroutine))
        else:
            self.sub_commands.append(SubCommand(sub_commands, self.coroutine))
        

class CacheableSubCommand:
    def __init__(
        self,
        name: str
    ):
        self.name = name
        self.map = {"sub_commands": {}, "groups": {}}

    def _map(self, incoming: TopLevelSubCommand):
        if incoming.group_name is None:
            for sub_command in incoming.sub_commands:
                self.map['sub_commands'][str(sub_command.name)] = sub_command
        else:
            self.map['groups'][str(incoming.group_name)] = {"sub_commands": {}}
            for sub_command in incoming.sub_commands:
                self.map['groups'][str(incoming.group_name)]['sub_commands'][str(sub_command.name)] = sub_command


class Command:
    def __init__(
        self,
        name: str,
        command_type: int,
        coroutine: Callable,
        requires_ack: bool,
        requires_ephemeral: bool
    ):
        self.name = name
        self.type = command_type
        self.coroutine = coroutine
        self.requires_ack = requires_ack
        self.requires_ephemeral = requires_ephemeral

    async def __call__(self, context):
        """Invokes the coroutine attached to the command."""
        try:
            response = await self.coroutine(context)
            if response is not None and type(response) == dict:
                return response
        except Exception as e:
            raise InvocationError(self.coroutine.__qualname__, e)


class Component:
    def __init__(
        self,
        name: str,
        coroutine: Callable,
        requires_ack: bool = False,
        requires_ephemeral: bool = False,
        timeout: float = 0.0
    ):
        self.name = name
        self.coroutine = coroutine
        self.requires_ack = requires_ack
        self.requires_ephemeral = requires_ephemeral
        self.timeout = timeout if timeout > 0.0 else None

    async def __call__(self, context):
        if self.timeout is not None:
            if ((datetime.now(timezone.utc) - datetime.fromisoformat(context.raw['message']['timestamp'])).total_seconds() > self.timeout):
                if not self.requires_ack:
                    return {"type": utils.CHANNEL_WITH_SOURCE, "data": {"content": "This component has timed out", "flags": 64}}

        try:
            response = await self.coroutine(context)
            if response is not None and type(response) == dict:
                return response
        except Exception as e:
            raise InvocationError(self.coroutine.__qualname__, e)


