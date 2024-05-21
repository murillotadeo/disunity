from __future__ import annotations


class EmptyEmbedError(Exception):
    def __init__(self, message):
        super().__init__(message)


class Embed:
    def __init__(
        self,
        title: None | str = None,
        description: None | str = None,
        color: None | int = None,
    ):
        self.__json: dict = {"type": "rich", "color": color}

        self._title: None | str = title
        self._description: None | str = description
        self._color: None | int = color

        self.title = title
        self.description = description

    @property
    def description(self) -> None | str:
        return self._description

    @description.setter
    def description(self, value: None | str) -> None:
        if value is not None:
            value = str(value)
        self._description = value
        self.__json["description"] = value

    @property
    def color(self) -> None | int:
        return self._color

    @color.setter
    def color(self, value: None | int) -> None:
        self._color = value
        self.__json["color"] = value

    @property
    def title(self) -> None | str:
        return self._title

    @title.setter
    def title(self, value: None | str) -> None:
        if value is not None:
            value = str(value)
        self._title = value
        self.__json["title"] = value

    @property
    def fields(self) -> None | list[dict]:
        return self.__json.get("fields", None)

    def add_field(self, name: str, value: str, inline: bool = False) -> Embed:
        if not bool(name) or not bool(value):
            raise EmptyEmbedError("Embed field cannot contain an empty value")

        if "fields" not in self.__json:
            self.__json["fields"] = []

        self.__json["fields"].append({"name": name, "value": value, "inline": inline})
        return self

    @property
    def footer(self) -> None | dict:
        return self.__json.get("footer", None)

    def set_footer(self, text: None | str = None, icon_url: None | str = None) -> Embed:
        if "footer" not in self.__json:
            self.__json["footer"] = {}

        if text is not None:
            self.__json["footer"]["text"] = str(text)

        if icon_url is not None:
            self.__json["footer"]["icon_url"] = str(icon_url)

        return self

    @property
    def image(self) -> None | dict:
        return self.__json.get("url", None)

    def set_image(self, image_url: str) -> Embed:
        if "image" not in self.__json:
            self.__json["image"] = {}

        self.__json["image"]["url"] = str(image_url)
        return self

    @property
    def thumbnail(self) -> None | dict:
        return self.__json.get("thumbnail", None)

    def set_thumbnail(self, thumbnail_url: str) -> Embed:
        if "thumbnail" not in self.__json:
            self.__json["thumbnail"] = {}

        self.__json["thumbnail"]["url"] = str(thumbnail_url)
        return self

    @property
    def author(self) -> None | dict:
        return self.__json.get("author", None)

    def set_author(
        self, name: str, url: None | str = None, icon_url: None | str = None
    ) -> Embed:
        if "author" not in self.__json:
            self.__json["author"] = {"name": str(name)}

        if url is not None:
            self.__json["author"]["url"] = str(url)

        if icon_url is not None:
            self.__json["author"]["icon_url"] = str(icon_url)

        return self

    def as_dict(self) -> dict:
        return self.__json
