from .. import utils


class User:
    def __init__(self, user_data):
        self.raw = user_data
        self.id = int(user_data['id'])
        self.discriminator = int(user_data['discriminator'])
        self.name = user_data['username']

    @property
    def avatar_url(self):
        return utils.return_avatar_as_cdn(self.raw['avatar'], self.id)

    @property
    def username(self):
        return self.name + '#' + str(self.discriminator)
