from ..errors import InvalidMethodUse
from .user import User
from .member import Member

class Interaction:
    def __init__(self, received):
        self.raw: dict = received
        self.app_permissions: None | int = received.get("app_permissions", None)
        if self.app_permissions is not None:
            self.app_permissions = int(self.app_permissions)

        self.channel_id: int = int(received["channel_id"])
        self.id: int = int(received["id"])
        self.locale: str = received["locale"]
        self.token: str = received["token"]
        self.interaction_type: int = int(received["type"])
        self.data: dict = received["data"]
        self.resolved: None | dict = self.data.get("resolved", None)
        self.component_type: None | int = self.data.get("component_type", None)
        self.custom_id: None | str = self.data.get("custom_id", None)
        self.values: list = self.data.get("values", [])
        self.member: None | Member = None
        self.used_by: None | User = None
        self.command_name: str = self.data.get("name", None)
        self.modal_values: None | list[dict] = None

        if 'member' in received: # Not a DM command
            self.invoked_by: User = User(received["member"]["user"])
            self.member = Member(received["member"])
        else:
            self.invoked_by: User = User(received["user"])

        if self.interaction_type == 3: # Component
            self.invoked_by: User = User(received["message"]["interaction"]["user"])
            if 'member' in received:
                self.used_by: None | User = User(received["member"]["user"])
            else:
                self.used_by: None | User = User(received["user"])

        elif self.interaction_type == 5: # modal submit
            self.modal_values: None | list[dict] = self.data["components"][0]["components"]   


    def check_user(self) -> bool:
        """
            For components, checks if the component user and
            the interaction author are the same.
        """

        if self.interaction_type != 3:
            raise InvalidMethodUse("Interaction is not a component interaction")

        if self.invoked_by.id == self.used_by.id:
            return True
        return False
