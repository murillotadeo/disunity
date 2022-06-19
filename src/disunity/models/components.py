from __future__ import annotations
from typing import Any, Optional, List, Union


class ActionRow:
    def __init__(
        self,
        components: List[Any[Button, SelectMenu]]
    ):
        self.dict = {"type": 1, "components": [component.to_dict() for component in components]}

    def to_dict(self):
        return self.dict


class ButtonStyles:
    PRIMARY = 1
    SECONDARY = 2
    SUCCESS = 3
    DANGER = 4
    LINK = 5


class Button:
    def __init__(
        self,
        custom_id: Union[str, None],
        label: str,
        style: Optional[int] = ButtonStyles.PRIMARY,
        emoji: Optional[dict] = {},
        url: Optional[str] = None,
        disabled: bool = False
    ):
        self.dict = {"type": 2, "custom_id": custom_id, "label": label, "style": style, "emoji": emoji, "disabled": disabled}

        if self.dict['style'] == ButtonStyles.LINK and url is not None:
            self.dict['url'] = url
    

    def to_dict(self):
        return self.dict


class SelectMenuOption:
    def __init__(
        self,
        label: str,
        value: Union[str, int],
        description: Optional[str] = "",
        emoji: Optional[dict] = {}
    ):
        self.dict = {"label": label, "value": value, "description": description, "emoji": emoji}

    def to_dict(self):
        return self.dict


class SelectMenu:
    def __init__(
        self,
        custom_id: str,
        options: List[SelectMenuOption],
        placeholder: Optional[str] = "",
        disabled: bool = False
    ):
        self.dict = {"type": 3, "custom_id": custom_id, "options": [option.to_dict() for option in options], "placeholder": placeholder, "disabled": disabled}

    def to_dict(self):
        return self.dict


class TextInputType:
    SHORT = 1
    PARAGRAPH = 2


class UserTextInput:
    def __init__(
        self, 
        custom_id: str,
        style: Optional[int],
        label: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = 4000,
        required: Optional[bool] = True,
        value: Optional[str] = None,
        placeholder: Optional[str] = None
    ):
        self.dict = {"type": 4, "custom_id": custom_id, "style": style, "label": label, "required": required, "max_length": max_length}

        if value is not None:
            self.dict.update(value=value)
        if placeholder is not None:
            self.dict.update(placeholder=placeholder)
        if min_length is not None:
            self.dict.update(min_length=min_length)

    def to_dict(self):
        return self.dict


class Modal:
    def __init__(
        self,
        title: str,
        custom_id: str,
        components: List[UserTextInput]
    ):
        self.dict = {"title": title, "custom_id": custom_id, "components": [ActionRow([comp]).to_dict() for comp in components]}

    def to_dict(self):
        return self.dict
