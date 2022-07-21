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

        self.title: None | str = title
        self.description: None | str = description
        self.color: None | int = color

        if self.title is not None:
            self.title = str(self.title)
            self.__json["title"] = self.title


        if self.description is not None:
            self.description = str(self.description)
            self.__json["description"] = self.description

    @property
    def fields(self) -> None | list[dict]:
        return self.__json.get("fields", None)

    def add_field(self, name: str, value: str, inline: bool = False) -> Embed:
        if not bool(name) or not bool(value):
            raise EmptyEmbedError("Embed field cannot contain an empty value")
        
        if 'fields' not in self.__json:
            self.__json["fields"] = []

        self.__json["fields"].append({"name": name, "value": value, "inline": inline})
        return self 

    @property
    def footer(self) -> None | dict:
        return self.__json.get("footer", None)

    def set_footer(self, text: None | str = None, icon_url: None | str = None) -> Embed:
        if 'footer' not in self.__json:
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
        if 'image' not in self.__json:
            self.__json["image"] = {}

        self.__json["image"]["url"] = str(image_url)
        return self

    @property
    def thumbnail(self) -> None | dict:
        return self.__json.get("thumbnail", None)

    def set_thumbnail(self, thumbnail_url: str) -> Embed:
        if 'thumbnail' not in self.__json:
            self.__json["thumbnail"] = {}

        self.__json["thumbnail"]["url"] = str(thumbnail_url)
        return self

    @property
    def author(self) -> None | dict:
        return self.__json.get("author", None)

    def set_author(self, name: str, url: None | str = None, icon_url: None | str = None) -> Embed:
        if 'author' not in self.__json:
            self.__json["author"] = {"name": str(name)}

        if url is not None:
            self.__json["author"]["url"] = str(url)

        if icon_url is not None:
            self.__json["author"]["icon_url"] = str(icon_url)

        return self

    def as_dict(self) -> dict:
        return self.__json
