from .. import utils
from ..errors import InvalidMethodUse
from .member import Member
from .user import User


class Interaction:
    def __init__(self, received):
        self.raw: dict = received
        self.app_permissions: int = int(received.get("app_permissions", 0))

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

        if "member" in received:  # Not a DM command
            self.invoked_by: User = User(received["member"]["user"])
            self.member = Member(received["member"])
        else:
            self.invoked_by: User = User(received["user"])

        if (
            self.interaction_type == utils.InteractionTypes.MESSAGE_COMPONENT
        ):  # Component
            if "interaction" in received["message"]:
                self.invoked_by: User = User(received["message"]["interaction"]["user"])
            else:
                self.invoked_by: User = None
            if "member" in received:
                self.used_by: None | User = User(received["member"]["user"])
            else:
                self.used_by: None | User = User(received["user"])

        elif (
            self.interaction_type == utils.InteractionTypes.MODAL_SUBMIT
        ):  # modal submit
            self.modal_values: None | list[dict] = self.data["components"][0][
                "components"
            ]

    def check_user(self) -> bool:
        """
        For components, checks if the component user and
        the interaction author are the same.
        """

        if self.interaction_type != utils.InteractionTypes.MESSAGE_COMPONENT:
            raise InvalidMethodUse("Interaction is not a component interaction")

        if self.invoked_by.id == self.used_by.id:
            return True
        return False
