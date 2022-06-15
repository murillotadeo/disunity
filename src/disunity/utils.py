from enum import Enum

SLASH_COMMAND = 1
USER_COMMAND = 2
MESSAGE_COMMAND = 3

CHANNEL_WITH_SOURCE = 4
DEFERRED_CHANNEL_WITH_SOURCE = 5
DEFERRED_UPDATE_MESSAGE = 6
UPDATE_MESSAGE = 7
MODAL = 9

T_PING = 1
T_SLASH_COMMAND = 2
T_COMPONENT = 3
T_MODAL_SUBMIT = 5

__version__ = '0.0.8'

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
        animated = avatar.startswith('a_')
        suffix = 'gif' if animated else 'png'
        return f"https://cdn.discordapp.com/avatars/{uid}/{avatar}.{suffix}?size=1024"
    return f"https://cdn.discordapp.com/embed/avatars/{uid%len(DefaultAvatars)}.png"
