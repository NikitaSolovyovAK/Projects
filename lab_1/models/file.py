from datetime import datetime
from typing import Dict, Any, Optional, Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .permission import Permissions
    from .file_format import FileFormat

from .filesystem_entry import FileSystemEntry

class File(FileSystemEntry):

    def __init__(self, name: str, owner: 'User', file_format: 'FileFormat',
                 content: Union[str, bytes] = b"", group: str = "users",
                 permissions: Optional["Permissions"] = None) -> None:
        super().__init__(name, owner, group, permissions)
        self._format = file_format

        if isinstance(content, str):
            self._content = content.encode('utf-8')
        else:
            self._content = content

    @property
    def format(self) -> 'FileFormat':
        return self._format

    @property
    def content(self) -> bytes:
        return self._content

    @content.setter
    def content(self, new_content: Union[str, bytes]) -> None:
        if isinstance(new_content, str):
            self._content = new_content.encode('utf-8')
        else:
            self._content = new_content
        self._update_modified()
        disk = self.disk
        if disk:
            disk.update_free_space()

    def get_size(self) -> int:
        return len(self._content)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "type": "file",
            "format": self._format.name,
            "content": self._content.hex()
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], users_map: Dict[str, 'User']) -> 'File':
        from .file_format import FileFormat
        from .permission import Permissions

        owner = users_map.get(data["owner"])
        if not owner:
            raise ValueError(f"Владелец с ID {data['owner']} не найден")

        permissions = Permissions.from_dict(data["permissions"])

        try:
            file_format = FileFormat[data["format"]]
        except KeyError:
            raise ValueError(f"Неизвестный формат файла: {data['format']}")

        content = bytes.fromhex(data["content"])

        #Создаем новый объект класса File и передаем в конструктор восстановленные значения
        file_obj = cls(
            name=data["name"],
            owner=owner,
            file_format=file_format,
            content=content,
            group=data["group"],
            permissions=permissions
        )

        if "created_at" in data:
            file_obj._created_at = datetime.fromisoformat(data["created_at"])
        if "modified_at" in data:
            file_obj._modified_at = datetime.fromisoformat(data["modified_at"])

        return file_obj

    def __str__(self) -> str:
        return f"File(name='{self.name}', format={self._format.name}, size={self.get_size()})"

    def __repr__(self) -> str:
        return f"File(name={self.name!r}, owner={self.owner.username}, format={self._format.name})"

