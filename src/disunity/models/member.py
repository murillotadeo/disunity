from .user import User
from .. import utils

class Member:
    def __init__(self, received: dict):
        self.raw: dict = received
        self.deaf: bool = received["deaf"]
        self.is_pending: bool = received["is_pending"]
        self.joined_at = received["joined_at"]
        self.mute: bool = received["mute"]
        self.nick: str = received["nick"]
        self.permissions: int = int(received["permissions"])
        self.roles: list[int] = [int(role) for role in received["roles"]]
        self.user: User = User(received["user"])
        self.flags: int = int(received["flags"])

    @property
    def server_avatar_url(self) -> None | str:
        if self.raw["avatar"] != "None":
            return utils.return_avatar_as_cdn(self.raw["avatar"], self.user.id)
        return None 
