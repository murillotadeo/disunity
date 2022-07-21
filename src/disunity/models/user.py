from .. import utils

class User:
    def __init__(self, received):
        self.raw: dict = received
        self.id: int = int(received["id"])
        self.name: str = received["username"]
        self.discriminator: int = int(received["discriminator"])
        self.avatar_decoration: str = received["avatar_decoration"]
        self.public_flags: int = int(received["public_flags"])

    @property
    def avatar_url(self) -> str:
        return utils.return_avatar_as_cdn(self.raw["avatar"], self.id)

    @property
    def username(self) -> str:
        return self.name + "#" + str(self.discriminator)

    @property
    def mention(self) -> str:
        return "<@!{}>".format(self.id)
