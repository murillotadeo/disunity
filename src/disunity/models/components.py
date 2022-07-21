from __future__ import annotations

class ButtonStyles:
    PRIMARY: int = 1
    SECONDARY: int = 2
    SUCCESS: int = 3
    DANGER: int = 4
    LINK: int = 5

class TextInputStyles:
    SHORT = 1
    PARAGRAPH = 2

class ActionRow:
    """
        Represents an action row object. 
        
        Parameters
        ----------
        components : list[Button | SelectMenu | Modal]
            Components to be contained within the action row. Limited to 5 buttons per action row
            or 1 select menu per action row.
    """
    def __init__(self, components: list[Button | SelectMenu | Modal | UserTextInput]):
        self.dict = {"type": 1, "components": [component.to_dict() for component in components]}
    
    def to_dict(self) -> dict:
        return self.dict 

class Button:
    """
        Represents a button component.

        Parameters
        ----------
        custom_id : str | None
            The custom id of the button. Only set to None when using a ButtonStyles.LINK button style.
        style: int
            The button style, recommended use is ButtonStyles
        emoji : dict
            The emoji to be displayed on the button.
        url : str
            For a ButtonStyles.LINK style button, the url where the button will take the user.
        disabled : bool
            Will the button be disabled. Default to False.
    """
    def __init__(
        self,
        custom_id: str | None,
        label: str,
        style: int = ButtonStyles.PRIMARY,
        emoji: dict = {},
        url: str | None = None,
        disabled: bool = False 
    ):
        self.dict = {"type": 2, "custom_id": custom_id, "label": label, "style": style, "emoji": emoji, "disabled": disabled}

        if self.dict['style'] == ButtonStyles.LINK and url is not None:
            self.dict['url'] = url

    def to_dict(self) -> dict:
        return self.dict

class SelectMenuOption:
    """
        Represents a select menu option.

        Parameters
        ----------
        label : str 
            The text that will be displayed for the option name
        value : str | int
            The value of the menu option
        description : str
            The description of the menu option. Optional.
        emoji : dict 
            The emoji to be displayed on the left of the menu option. Optional.
    """
    def __init__(
        self,
        label: str,
        value: str | int,
        description: str = "",
        emoji: dict = {}
    ):
        self.dict = {"label": label, "value": value, "description": description, "emoji": emoji}

    def to_dict(self) -> dict:
        return self.dict

class MenuOption(SelectMenuOption):
    """Alias class for SelectMenuOption."""
    def __init__(
        self,
        label: str,
        value: str | int,
        description: str = "",
        emoji: dict = {}
    ):
        super().__init__(
            label,
            value,
            description,
            emoji
        )


class SelectMenu:
    """
        Represents a select menu component object

        Parameters
        ----------
        custom_id : str
            The custom id for this component
        options : list[SelectMenuOption | MenuOption]
            The options to be displayed for this menu. Maximum of 25.
        placeholder : str
            Placeholder text for the menu
        disabled : bool 
            Is the menu disabled or not 
    """
    def __init__(
        self,
        custom_id: str,
        options: list[SelectMenuOption | MenuOption],
        placeholder: str = "",
        disabled: bool = False
    ):
        if len(options) > 25:
            raise ValueError("SelectMenu cannot contain more than 25 options.")

        self.dict = {"type": 3, "custom_id": custom_id, "options": [option.to_dict() for option in options], "placeholder": placeholder, "disabled": disabled}

    def to_dict(self) -> dict:
        return self.dict 

class UserTextInput:
    """
        Represnets a user text input prompt (modal)
        Parameters
        ----------
        custom_id : str
            The custom id for this input prompt 
        label : str
            The label for this input prompt 
        style : int | TextInputStyle
            The style of the text input. 1 for short, 2 for paragraph.
        min_length : int 
            Minimum length for the input
        max_length : int
            The maximum length of the input, defaulted to 4000 characters.
        required : bool
            Is the input required, defaulted to False
        value : str | None
            The value of the input
        placeholder : str
            Placeholder test for the input 
    """
    def __init__(
        self,
        custom_id: str,
        label: str,
        style: int = TextInputStyles.SHORT,
        min_length: int | None = None,
        max_length: int = 4000,
        required: bool = False,
        value: str | None = None,
        placeholder: str | None = None 
    ):
        self.dict = {"type": 4, "custom_id": custom_id, "style": style, "label": label, "required": required, "max_length": max_length}
 
        if value is not None:
            self.dict['value'] = value
        elif placeholder is not None:
            self.dict['placeholder'] = placeholder
        elif min_length is not None:
            self.dict['min_length'] = min_length

    def to_dict(self) -> dict:
        return self.dict

class Modal:
    """
        Represents a Modal component object.

        Parameters
        ----------
        title : str
            The title of the Modal
        custom_id : str
            The custom id of the component
        components : list[UserTextInput]
            The inputs to ask the user.
    """
    def __init__(
        self,
        title: str,
        custom_id: str,
        components: list[UserTextInput]
    ):
        if len(components) == 0:
            raise ValueError("Components list cannot be empty.")

        self.dict = {"title": title, "custom_id": custom_id, "components": [ActionRow([comp]).to_dict() for comp in components]}

    def to_dict(self) -> dict:
        return self.dict 
