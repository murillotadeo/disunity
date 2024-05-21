from __future__ import annotations

from ..embed import Embed
from .components import ActionRow
from .user import User


class MissingTokenError(Exception):
    def __init__(self, func_name):
        super().__init__(f"A bot token is required to use the {func_name} method")


class ExpiredInteractionError(Exception):
    def __init__(self):
        super().__init__(
            "The token belonging to this interaction has expired or leads to an unkown webhook"
        )


class Message:
    def __init__(self, raw_message, server, token=None):
        self.server = server
        self.raw: dict = raw_message
        self.id: int = int(raw_message["id"])
        self.author: User | dict = raw_message.get("author", None)
        if self.author is not None:
            self.author: User | dict = User(self.author)

        self.channel_id: int = raw_message["channel_id"]
        self.components: list[dict] | list = raw_message["components"]
        self.embeds: list | list[dict] = raw_message["embeds"]
        self.attachments: list | list[dict] = raw_message.get("attachements")
        self.content: str = raw_message["content"]
        self.interaction_token: str | None = token

    def remake(self, new_raw):
        self.raw = new_raw
        self.content = self.raw["content"]
        self.embeds = self.raw["embeds"]
        self.components = self.raw["components"]

    async def edit_as_webhook(
        self,
        content: None | str = None,
        embeds: None | list[Embed] | Embed = None,
        components: None | list[ActionRow] | ActionRow = None,
    ) -> Message:
        if isinstance(embeds, Embed):
            embeds = [embeds]
        if isinstance(components, ActionRow):
            components = [components]

        message_body = self.raw
        message_body["content"] = str(content) if content is not None else self.content
        message_body["embeds"] = (
            [emb.as_dict() for emb in embeds if isinstance(emb, Embed)]
            if embeds is not None
            else self.embeds
        )
        message_body["components"] = (
            [row.to_dict() for row in components if isinstance(row, ActionRow)]
            if components is not None
            else self.components
        )

        attempt = await self.server.make_https_request(
            "PATCH",
            f"webhooks/{self.server.config['CLIENT_ID']}/{self.interaction_token}/messages/{self.id}",
            payload=message_body,
            override_checks=True,
        )

        if not str(attempt.status).startswith("20"):
            recv = await attempt.json()
            if recv["code"] in [10015, 50027]:
                raise ExpiredInteractionError

        self.remake(message_body)
        return self

    async def edit_as_bot(
        self,
        content: None | str = None,
        embeds: None | list[Embed] | Embed = None,
        components: None | list[ActionRow] | ActionRow = None,
    ) -> Message:
        if self.server.config["BOT_TOKEN"] is None:
            raise MissingTokenError("Message.edit_as_bot")

        if isinstance(embeds, Embed):
            embeds = [embeds]
        if isinstance(components, ActionRow):
            components = [components]

        message_body = self.raw
        message_body["content"] = str(content) if content is not None else self.content
        message_body["embeds"] = (
            [emb.as_dict() for emb in embeds if isinstance(emb, Embed)]
            if embeds is not None
            else self.embeds
        )
        message_body["components"] = (
            [row.to_dict() for row in components if isinstance(row, ActionRow)]
            if components is not None
            else self.components
        )

        await self.server.make_https_request(
            "PATCH",
            f"channels/{self.channel_id}/messages/{self.id}",
            payload=message_body,
        )

        self.remake(message_body)
        return self

    async def delete_as_webhook(self):
        await self.server.make_https_request(
            "DELETE",
            f"webhooks/{self.server.config['CLIENT_ID']}/{self.interaction_token}/messages/{self.id}",
        )

    async def delete_as_bot(self):
        if self.server.config["BOT_TOKEN"] is None:
            raise MissingTokenError("Message.delete_as_bot")

        await self.server.make_https_request(
            "DELETE", f"channels/{self.channel_id}/messages/{self.id}"
        )
