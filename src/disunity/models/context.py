from typing import List, Optional
from ..embed import Embed
from .components import ActionRow

class DisunityCommandContext:
    def __init__(self, app, response):
        self.__app = app
        self.raw = response
        self.command_name = response['data'].get('name', None)
        self.command_id = response['data'].get('id', None)
        self.channel_id = response.get('channel_id', None)
        self.id = response.get('id', None)
        self.token = response.get('token', None)
        self.type = response.get('type', None)
        self.invoked_by = response['member']['user']
        self.resolved = response['data'].get('resolved', None)
        self.acked = False
    
    async def callback(self, content: str = '', embed: Optional[Embed] = None, embeds: Optional[List[Embed]] = [], components: list = [], allowed_mentions: list = [], ephemeral: bool = False):
        """
            Creates the first interation response.
            
            Parameters
            ----------
            content: str
                The content of the message

            embed: disunity.Embed
                The embed to send along with the message

            embeds: List[disunity.Embed]
                List of embeds to send, will all be shown at once

            allowed_mentions: list
                Allowed mentions of the message

            ephemeral: bool
                Will the message show publically or privately 
        """
        
        if self.acked:
            ... # Remind myself to raise an error here or something
        
        _embeds = []
        if len(list(embeds)) > 0 and embed is not None:
            _embeds = embeds.insert(0, embed)
        
        elif embed is not None and len(list(embeds)) == 0:
            _embeds = [embed]

        else:
            _embeds.extend(embeds)

        message_body = {
            "type": 4,
            "data": {
                "content": content,
                "embeds": [emb.to_dict() for emb in _embeds if isinstance(emb, Embed)],
                "components": [ar.to_dict() for ar in components if isinstance(ar, ActionRow)],
                "allowed_mentions": allowed_mentions
            }
        }
        if ephemeral:
            message_body['data']['flags'] = 64
        
        self.acked = True
        return message_body
