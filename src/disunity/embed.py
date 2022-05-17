from __future__ import annotations
from typing import Any, Optional 


class Embed:
    def __init__(
        self, 
        color = None,
        title: Optional[Any] = None,
        description: Optional[Any] = None,
    ):

        self.color = color
        self.title: Optional[str] = title
        self.description: Optional[str] = description
        self.__built = {}
    
    def add_field(self, name: str = None, value: str = None, inline: Optional[bool] = False):
        """Adds a field object to the Embed"""
        if name is None or value is None:
            _val = "name" if name is None else "value"
            raise ValueError(f"Embed.field.{_val} expected string, received NoneType")

        if name is None and value is None:
            raise ValueError("Embed.field object cannot be empty")

        try:
            self.__built['fields'].append({"name": name, "value": value, "inline": inline})
        except KeyError:
            self.__built['fields'] = [{"name": name, "value": value, "inline": inline}]

        return self

    def set_footer(self, text: str = None, icon_url: str = None):
        if text is None and icon_url is None:
            raise ValueError("Embed.footer object cannot be empty")

        try:
            self.__built['footer']['text'] = text
            if icon_url is not None:
                self.__built['footer']['icon_url'] = icon_url
        except KeyError:
            self.__built['footer'] = {"text": text}
            if icon_url is not None:
                self.__built['footer']['icon_url'] = icon_url

        return self

    def set_author(self, name: str = None, url: str = None, icon_url: str = None):
        if name is None and url is None and icon_url is None:
            raise ValueError("Embed.author object cannot be empty.")

        try:
            if name is not None:
                self.__built['author']['name'] = name
            if url is not None:
                self.__built['author']['url'] = url
            if icon_url is not None:
                self.__built['author']['icon_url'] = icon_url
        except KeyError:
            self.__built['author'] = {}
            if name is not None:
                self.__built['author']['name'] = name
            if url is not None:
                self.__built['author']['url'] = url
            if icon_url is not None:
                self.__built['author']['icon_url'] = icon_url

        return self

    def set_image(self, image_url: str):
        self.__built['image'] = {}
        self.__built['image']['url'] = str(image_url)

        return self

    def set_thumbnail(self, thumbnail_url: str):
        self.__built['thumbnail'] = {}
        self.__built['thumbnail']['url'] = thumbnail_url

        return self 

    def to_dict(self) -> dict:
        self.__built['type'] = "rich"
        self.__built['title'] = self.title
        self.__built['description'] = self.description
        self.__built['color'] = self.color

        return self.__built
