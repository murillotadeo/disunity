from .. import utils, errors, embed
from .interaction import Interaction
from .components import ActionRow, Modal
from .message import Message

class Context(Interaction):
    def __init__(self, app, received: dict):
        super().__init__(received)
        self._app = app
        self.acked: bool = False
        self.options = {}

        if 'data' in received:
            for option in received["data"].get("injected", []):
                self.options[option["name"]] = option["value"]

    async def callback(
        self,
        content: None | str = None,
        embeds: list[embed.Embed] | embed.Embed = [],
        components: list[ActionRow] | ActionRow = [],
        ephemeral: bool = False,
        response_type: int = utils.CHANNEL_WITH_SOURCE
    ) -> dict:
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
            response_type: int
                Callback interaction type
        """
        
        if isinstance(embeds, embed.Embed):
            embeds = [embeds]
        if isinstance(components, ActionRow):
            components = [components]
        
        message_body = {
            "type": response_type,
            "data": {
                "content": str(content) if content is not None else '',
                "embeds": [e.as_dict() for e in embeds if isinstance(e, embed.Embed)],
                "components": [row.to_dict() for row in components if isinstance(row, ActionRow)]
            }
        }

        if ephemeral:
            message_body["data"]["flags"] = 64 

        self.acked = True
        return message_body

    async def followup(
        self,
        content: None | str = None,
        embeds: list[embed.Embed] | embed.Embed = [],
        components: list[ActionRow] | ActionRow = [],
        ephemeral: bool = False 
    ) -> Message:
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
            ephemeral: bool
                Will the message show publically or privately 
        """

        if not self.acked:
            raise errors.InvalidMethodUse("Cannot followup an interaction that hasn't been acked")

        if isinstance(embeds, embed.Embed):
            embeds = [embeds]
        if isinstance(components, ActionRow):
            components = [components]

        message_body = {
            "content": str(content) if content is not None else '',
            "embeds": [e.as_dict() for e in embeds if isinstance(e, embed.Embed)],
            "components": [row.to_dict() for row in components if isinstance(row, ActionRow)]
        }

        if ephemeral:
            message_body["data"] = {"flags": 64}

        maybe_message = await self._app.make_https_request(
            "POST",
            f"webhooks/{self._app.config['CLIENT_ID']}/{self.token}",
            payload=message_body
        )

        return Message(maybe_message, self._app, self.token)


    async def modal_response(self, modal: Modal):
        """
            Responds to the interaction with a modal.

            Parameters
            ----------
            modal : components.Modal 
                The modal to respond with.
        """

        return {"type": 9, "data": modal.to_dict()}
