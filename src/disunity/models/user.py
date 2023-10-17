from .. import utils


class User:
    def __init__(self, received):
        self.raw: dict = received
        self.id: int = int(received["id"])
        self.name: str = received["username"]
        self.global_name: str = received["global_name"]
        self.discriminator: int = int(received["discriminator"])
        self.avatar_decoration: str = received.get("avatar_decoration", "")
        self.public_flags: int = int(received.get("public_flags", 0))

    @property
    def avatar_url(self) -> str:
        return utils.return_avatar_as_cdn(self.raw["avatar"], self.id)

    @property
    def username(self) -> str:
        return self.name + "#" + str(self.discriminator)

    @property
    def mention(self) -> str:
        return f"<@!{self.id}>"
