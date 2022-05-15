from datetime import datetime

class Command:
    def __init__(self, command_name, command_type, coroutine, requires_ephemeral: bool = False, requires_ack: bool = False):
        self.name = command_name
        self.type = command_type
        self.coro = coroutine
        self.requires_ephemeral = requires_ephemeral
        self.requires_ack = requires_ack

    async def __call__(self, context):
        try:
            await self.coro(context)
        except Exception as e:
            raise e

class Component:
    def __init__(self, parent_context, custom_id, coroutine, timeout: float = 0.0, is_single_use: bool = True, requires_ack: bool = False, requires_ephemeral: bool = False):
        self.parent = parent_context
        self.custom_id = custom_id
        self.coro = coroutine
        self.timeout = ((datetime.utcnow() - datetime.fromtimestamp(0)).total_seconds() + timeout) if timeout > 0.0 else 0.0
        self.is_single_use = is_single_use
        self.requires_ephemeral = requires_ephemeral
        self.requires_ack = requires_ack

    async def __call__(self, app, context):
        if self.timeout > 0.0:
            if (datetime.utcnow() - datetime.fromtimestamp(0)).total_seconds() > self.timeout:
                del app._warehouse.components[self.custom_id]
                return await context.reply("This component has timed out.")

            if self.is_single_use:
                del app._warehouse.components[self.custom_id]
                return

        await self.coro(context)
