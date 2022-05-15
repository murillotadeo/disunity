class ActionRow:
    def __init__(self, components: list = []):
        self.dict = {"type": 1, "components": [comp.to_dict() for comp in components]}

    def to_dict(self):
        if len(self.dict['components']) == 0:
            raise ValueError("Components array cannot be empty.")
        return self.dict

class Button:
    def __init__(self, custom_id, label, style, url=None, emoji=None):
        self.dict = {"type": 2, "custom_id": custom_id, "label": label, "style": style}
        self._emoji = emoji
        self._url = url
        self._style = style

    def to_dict(self):
        if self._style == ButtonStyle.LINK and self._url is not None:
            self.dict['url'] = self._url

        if self._emoji is not None:
            self.dict['emoji'] = self._emoji

        return self.dict

class SelectMenu:
    def __init__(self, custom_id: str, options: list, placeholder: str = ''):
        self.dict = {"type": 3, "custom_id": custom_id, "options": [opt.to_dict() for opt in options if isinstance(opt, SelectMenuOption)], "placeholder": placeholder}

    def to_dict(self):
        return self.dict

class SelectMenuOption:
    def __init__(self, label: str, value, description: str = '', emoji: dict = {}):
        self.dict = {"label": label, "value": value, "description": description, "emoji": emoji}

    def to_dict(self):
        if self.dict['value'] is None:
            raise ValueError("SelectMenuOption.value cannot be type NoneType")
        return self.dict

class ButtonStyle:
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5
