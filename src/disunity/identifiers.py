from datetime import datetime
from typing import Callable

class DisunityCommand:
    def __init__(
        self, 
        name: str,
        _type: int, 
        coroutine: Callable,
        requires_ack: bool = False,
        requires_ephemeral: bool = False
     ):

        self.name: str = name
        self.type: int = _type
        self.coroutine: Callable = coroutine
        self.requires_ack: bool = requires_ack
        self.requires_ephemeral: bool = requires_ephemeral

    async def __call__(self, context):
        """Invokes the coroutine attached to the command"""
            
        try:

            rjson = await self.coroutine(context)
            if type(rjson) == dict:
                return rjson
        
        except Exception as e:
            if not self.requires_ack:
                return await context.callback("There was an error when executing this command, plase contact the application developers.", ephemeral=True)
            print(e)

    
class DisunityComponent:
    def __init__(
        self,
        parent_context,
        custom_id: str,
        coroutine: Callable,
        timeout: float = 0.0,
        is_single_use: bool = True,
        requires_ack: bool = False,
        requires_ephemeral: bool = False
    ):
        
        self.parent = parent_context
        self.custom_id = custom_id
        self.coroutine = coroutine
        self.timeout = ((datetime.utcnow() - datetime.fromtimestamp(0)).total_seconds() + timeout) if timeout > 0.0 else None
        self.is_single_use: bool = is_single_use
        self.requires_ack: bool = requires_ack
        self.requires_ephemeral: bool = requires_ephemeral

    async def __call__(self, app, context):
        if self.timeout is not None:
            if (datetime.utcnow() - datetime.fromtimestamp(0)).total_seconds() > self.timeout:
                del app._cache.components[self.custom_id]

                if self.requires_ack:
                    return await context.reply("This component has timed out.")
                else:
                    return await context.callback("This component has timed out.", ephemeral=True)
                
        if self.is_single_use:
            del app._cache.components[self.custom_id]
        
        try:

            rjson = await self.coroutine(context)
            if type(rjson) == dict:
                return rjson

        except Exception as e:
            if not self.requires_ack:
                return await context.callback("There was an error when executing this component, please contact the application developers", ephemeral=True)
            print(e)

