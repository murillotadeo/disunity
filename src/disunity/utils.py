from enum import Enum

# Set application command types
SLASH = 2
USER = 2
MESSAGE = 3

# Set message response types
CHANNEL_WITH_SOURCE = 4
DEFERRED_CHANNEL_WITH_SOURCE = 5
DEFERRED_UPDATE_MESSAGE = 6
UPDATE_MESSAGE = 7
AUTOCOMPLETE_RESULT = 8

__version__ = '0.1.0'


class Avatars(Enum):
    """
    Enum for Discord avatars
    """

    blurple = 0
    grey = 1
    gray = 1
    green = 2
    orange = 3
    red = 4

    def __str__(self):
        return self.name

def return_cdn_avatar(data):
    if data['avatar'] is not None:
        animated = data['avatar'].startswith('a_')
        suffix = 'gif' if animated else 'png'
        return f'https://cdn.discordapp.com/avatars/{data["id"]}/{data["avatar"]}.{suffix}?size=1024'
    else:
        return f"https://cdn.discordapp.com/embed/avatars/{int(data['id']) % len(Avatars)}.png"
