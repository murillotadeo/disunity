from enum import Enum, IntEnum

__version__ = "0.1.3"


class InteractionTypes(IntEnum):
    PING = 1
    APPLICATION_COMMAND = 2
    MESSAGE_COMPONENT = 3
    APPLICATION_COMMAND_AUTOCOMPLETE = 4
    MODAL_SUBMIT = 5


class InteractionCallbackTypes(IntEnum):
    PONG = 1
    CHANNEL_MESSAGE_WITH_SOURCE = 4
    DEFERRED_CHANNEL_MESSAGE_WITH_SOURCE = 5
    DEFERRED_UPDATE_MESSAGE = 6
    UPDATE_MESSAGE = 7
    APPLICATION_COMMAND_AUTOCOMPLETE_RESULT = 8
    MODAL = 9
    PREMIUM_REQUIRED = 10


class DefaultAvatars(Enum):
    blurple = 0
    grey = 1
    gray = 1
    green = 2
    orange = 3
    red = 4

    def __str__(self):
        return self.name


def return_avatar_as_cdn(avatar, uid):
    if avatar is not None:
        animated = avatar.startswith("a_")
        suffix = "gif" if animated else "png"
        return f"https://cdn.discordapp.com/avatars/{uid}/{avatar}.{suffix}?size=1024"
    return f"https://cdn.discordapp.com/embed/avatars/{uid%len(DefaultAvatars)}.png"
