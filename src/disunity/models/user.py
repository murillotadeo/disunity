from .. import utils

class User:
    def __init__(self, user_data): 
        self.raw = user_data
        self.id = int(user_data['id']) # Discord sends the ID as strings
        self.discriminator = int(user_data['discriminator']) # Sent as string
        self.name = user_data['username']

    @property
    def avatar_url(self):
        return utils.return_cdn_avatar(self.raw)

    @property
    def username(self):
        return self.name + '#' + str(self.discriminator)
