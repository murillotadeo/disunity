from typing import List, Optional
from ...embed import Embed
from .components import ActionRow
from .user import User

class WebCommandContext:
    def __init__(self, quart_app, web_response): 
        self._app = quart_app
        self.raw = web_response
        self.name = web_response['data'].get('name', None)
        self.command_id = web_response['data'].get('id', None)
        self.channel_id = web_response.get('channel_id', None)
        self.interaction_id = web_response['data'].get('id', None)
        self.token = web_response.get('token', None)
        self.type = web_response.get('type', None)
        self.invoked_by = User(web_response['member']['user'])
        self.options = dict()
        self.resolved = web_response['data'].get('resolved', None)

        for option in web_response['data'].get('options', []):
            self.options[option['name']] = option['value']

    async def reply(self, content: str = '', embed: Optional[Embed] = None, embeds: Optional[List[Embed]] = [], components: Optional[List[ActionRow]] = []):
        """Replies to the acked interaction"""
        _embeds = []
        if len(list(embeds)) > 0 and embed is not None:
            _embeds = embeds.insert(0, embed)
        
        elif embed is not None and len(list(embeds)) == 0:
            _embeds = [embed]

        else:
            _embeds = embeds

        response_json = {
            "type": 4,
            "content": content,
            "embeds": [emb.build() for emb in _embeds if isinstance(emb, Embed)],
            "components": [c.to_dict() for c in components if isinstance(c, ActionRow)]
        }

        await self._app.make_http_request('POST', f"webhooks/{self._app.config['CLIENT_ID']}/{self.token}", payload=response_json)

class WebComponentContext(WebCommandContext):
    def __init__(self, quart_app, web_response):
        self._app = quart_app
        self.raw = web_response
        
        self.custom_id = self.raw['data']['custom_id']
        self.invoked_by = User(self.raw['message']['interaction']['user'])
        self.used_by = User(self.raw['member']['user'])
        self.values = self.raw['data'].get('values', None)
