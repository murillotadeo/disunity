class Attachment:
    def __init__(self, filename: str, content: bytes, description: str = None):
        self._filename = filename
        self._content = content
        self._description = description

    @property
    def filename(self) -> str:
        return self._filename

    @filename.setter
    def filename(self, value: str) -> None:
        self._filename = value

    @property
    def description(self) -> str:
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._description = value

    @property
    def content(self) -> bytes:
        return self._content

    @content.setter
    def content(self, value: bytes) -> None:
        self._content = value

    def as_dict(self) -> dict:
        return {
            "filename": self._filename,
            "description": self._description,
            "content": self._content,
        }
