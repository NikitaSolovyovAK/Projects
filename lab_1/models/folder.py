from datetime import datetime
from typing import Dict, List, Optional, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .permission import Permissions
    from .filesystem_entry import FileSystemEntry

from .filesystem_entry import FileSystemEntry


class Folder(FileSystemEntry):
    def __init__(
        self,
        name: str,
        owner: 'User',
        group: str = "users",
        permissions: Optional['Permissions'] = None
    ) -> None:
        super().__init__(name, owner, group, permissions)
        self._children: Dict[str, 'FileSystemEntry'] = {}
        self._disk: Optional['Disk'] = None

    def add_entry(self, entry: 'FileSystemEntry') -> None:
        if entry.name in self._children:
            raise FileExistsError(f"Элемент с именем '{entry.name}' уже существует в папке '{self.name}'")
        self._children[entry.name] = entry
        entry._parent = (#установление родительской ссылки для добавляемого элемента
            self)
        self._update_modified()
        disk = self.disk
        if disk:
            disk.update_free_space()

    def remove_entry(self, name: str) -> None:
        if name not in self._children:
            raise FileNotFoundError(f"Элемент '{name}' не найден в папке '{self.name}'")
        entry = self._children.pop(name)
        entry._parent = None
        self._update_modified()
        disk = self.disk
        if disk:
            disk.update_free_space()

    def get_entry(self, name: str) -> 'FileSystemEntry':
        if name not in self._children:
            raise FileNotFoundError(f"Элемент '{name}' не найден в папке '{self.name}'")
        return self._children[name]

    def list_entries(self) -> List[str]:
        return list(self._children.keys())

    def get_size(self) -> int:
        return sum(entry.get_size() for entry in self._children.values())

    def get_files(self) -> List['File']:
        from .file import File
        return [entry for entry in self._children.values() if isinstance(entry, File)]

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        children_list = [child.to_dict() for child in self._children.values()]#дочерние элементы сериализуются в свой словарь рекурсивно так как элементами могут быть и папки
        data.update({
            "type": "folder",
            "children": children_list
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any], users_map: Dict[str, 'User']) -> 'Folder':
        from .permission import Permissions
        from .file import File

        owner_id = data["owner"]#извлекается идентификатор пользователя и ищется пользователь соответствующий
        owner = users_map.get(owner_id)
        if not owner:
            raise ValueError(f"Владелец с ID {owner_id} не найден")

        permissions = Permissions.from_dict(data["permissions"])

        folder = cls(
            name=data["name"],
            owner=owner,
            group=data["group"],
            permissions=permissions
        )

        if "created_at" in data:
            folder._created_at = datetime.fromisoformat(data["created_at"])
        if "modified_at" in data:
            folder._modified_at = datetime.fromisoformat(data["modified_at"])

        children_data = data.get("children", [])
        for child_data in children_data:
            child_type = child_data.get("type")
            if child_type == "file":
                child = File.from_dict(child_data, users_map)
            elif child_type == "folder":
                child = Folder.from_dict(child_data, users_map)
            else:
                raise ValueError(f"Неизвестный тип элемента: {child_type}")
            child._parent = folder
            folder._children[child.name] = child
        return folder

    def __str__(self) -> str:
        return f"Folder(name='{self.name}', children={len(self._children)})"

    def __repr__(self) -> str:
        return f"Folder(name={self.name!r}, owner={self.owner.username})"