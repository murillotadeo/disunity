from .. import utils, errors
from .components import ActionRow
from ..embed import Embed
from .user import User


class CommandContext:
    def __init__(
        self, 
        app, 
        received
    ):
        self.__app = app
        self.raw = received
        self.command_name = received['data'].get('name', None)
        self.command_id = received['data'].get('id', None)
        self.channel_id = received.get('channel_id', None)
        self.invoked_by = User(received['member']['user'])
        self.resolved = received['data'].get('resolved', None)
        self.id = received.get('id', None)
        self.token = received.get('token', None)
        self.type = received.get('type', None)
        self.acked = False
        self.options = {}
        for option in received['data'].get('injected', []):
            self.options[option['name']] = option['value']


    async def callback(self, content: str = '', embeds: list[Embed] | Embed = [], components: list[ActionRow] | ActionRow = [], allowed_mentions: list = [], ephemeral: bool = False, response_type: int = utils.CHANNEL_WITH_SOURCE):
        """
            Creates the first interation response.
            
            Parameters
            ----------
            content: str
                The content of the message
            embeds: List[disunity.Embed] | disunity.Embed
                List of embeds to send, will all be shown at once
            components: List[ActionRow] | ActionRow:
                List of components to send.
            allowed_mentions: list
                Allowed mentions of the message
            ephemeral: bool
                Will the message show publically or privately
            type: int
                Callback interaction type
        """
       
        if isinstance(embeds, Embed):
            embeds = [embeds]
        if isinstance(components, ActionRow):
            components = [components]

        message_body = {
            "type": response_type,
            "data": {
                "content": str(content),
                "embeds": [embed.to_dict() for embed in embeds if isinstance(embed, Embed)],
                "components": [row.to_dict() for row in components if isinstance(row, ActionRow)],
                "allowed_mentions": allowed_mentions
            }
        }

        if ephemeral:
            message_body['data']['flags'] = 64
        
        self.acked = True
        return message_body

    
    async def follwup(self, content: str = '', embeds: list[Embed] | Embed = [], components: list[ActionRow] | ActionRow = [], ephemeral: bool = False):
        """
            Used to create a follow up response to an already acked interaction.
            Parameters
            ----------
            content: str
                The content of the message
            embeds: List[disunity.Embed] | disunity.Embed
                List of embeds to send, will all be shown at once
            components: List[ActionRow] | ActionRow:
                List of components to send with the message
            allowed_mentions: list
                Allowed mentions of the message
            ephemeral: bool
                Will the message show publically or privately 
        """

        if not self.acked:
            raise errors.InvalidMethodUse("Cannot followup an interaction that hasn't been acked, try using the callback method instead")

        if isinstance(embeds, Embed):
            embeds = [embeds]
        if isinstance(components, ActionRow):
            components = [components]

        message_body = {
            "content": str(content),
            "embeds": [embed.to_dict() for embed in embeds if isinstance(embed, Embed)],
            "components": [row.to_dict() for row in components if isinstance(row, ActionRow)]
        }

        if ephemeral:
            message_body['data']['flags'] = 64

        maybe_send = await self.__app.make_https_request(
            "POST",
            f"webhooks/{self.__app.config['CLIENT_ID']}/{self.token}",
            payload=message_body
        )
        return maybe_send

    

class ComponentContext(CommandContext):
    def __init__(self, app, received):
        super().__init__(app, received)

        self.custom_id = received['data']['custom_id']
        self.invoked_by = User(received['message']['interaction']['user'])
        self.used_by = User(received['member']['user'])
        self.values = received['data'].get('values', None)
