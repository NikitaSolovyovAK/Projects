import uuid
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .folder import Folder
    from .user import User
    from .filesystem_entry import FileSystemEntry

class Disk:
    def __init__(self, name: str, total_space: int, filesystem: str = "NTFS",
                 owner_id: Optional[str] = None, label: str = "", disk_id: Optional[str] = None):
        if total_space <= 0:
            raise ValueError("total_space должен быть положительным")
        self.disk_id = disk_id or str(uuid.uuid4())[:8]
        self.name = name
        self._label = label
        self.total_space = total_space
        self.free_space = total_space
        self.filesystem = filesystem
        self.owner_id = owner_id
        self.created_at = datetime.now()
        self.mounted = True
        self._root = None

    @property
    def label(self) -> str:
        return self._label

    @label.setter
    def label(self, new_label: str) -> None:
        self._label = new_label

    @property#геттер для корневой папки
    def root(self) -> 'Folder':
        if self._root is None:
            raise ValueError("Диск не отформатирован. Сначала выполните форматирование.")
        return self._root

    @root.setter
    def root(self, folder: 'Folder') -> None:
        self._root = folder

    #Создает корневую папку и связывает ее с диском
    def format(self, owner: 'User') -> None:
        from .folder import Folder
        self._root = Folder("/", owner)
        self._root._disk = self
        self.free_space = self.total_space

        self._root.permissions.owner = 7
        self._root.permissions.group = 5
        self._root.permissions.other = 5
        self.free_space = self.total_space

    def update_free_space(self) -> None:
        if self._root is not None:
            used = self._root.get_size()
            self.free_space = self.total_space - used
        else:
            self.free_space = self.total_space

    #Метод преобразует строку пути(абсолютного или относительно) в объект класса FileSystemEntry
    def resolve_path(self, path: str, current_folder: 'Folder') -> Optional['FileSystemEntry']:
        from .folder import Folder
        if path.startswith('/'):
            parts = path.strip('/').split('/') if path != '/' else []
            current = self.root #текущий элемент устанавливается в корневую папку диска
        else:
            parts = path.split('/')
            current = current_folder # текущий элемент - переданная current_folder
        for part in parts:
            if not part or part == '.':
                continue
            if part == '..':
                current = current.parent if current.parent else current
                continue
            if isinstance(current, Folder):
                try:
                    current = current.get_entry(part)
                except FileNotFoundError:
                    return None
            else:
                return None
        return current #после всего возвращает найденный элемент

    def to_dict(self) -> Dict[str, Any]:
        return {
            "disk_id": self.disk_id,
            "name": self.name,
            "label": self._label,
            "total_space": self.total_space,
            "free_space": self.free_space,
            "filesystem": self.filesystem,
            "owner_id": self.owner_id,
            "created_at": self.created_at.isoformat(),
            "mounted": self.mounted,
            "root": self._root.to_dict() if self._root else None,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], users_map: Dict[str, 'User']) -> 'Disk':
        disk = cls(
            name=data["name"],
            total_space=data["total_space"],
            filesystem=data.get("filesystem", "NTFS"),
            owner_id=data.get("owner_id"),
            label=data.get("label", ""),
            disk_id=data.get("disk_id")
        )
        disk.free_space = data["free_space"]
        disk.created_at = datetime.fromisoformat(data["created_at"])
        disk.mounted = data.get("mounted", True)
        root_data = data.get("root")
        if root_data: #восстановление корневой папки и родительские связи
            from .folder import Folder
            disk._root = Folder.from_dict(root_data, users_map)
            disk._root._disk = disk
            disk._restore_parents(disk._root)
        return disk

    def _restore_parents(self, folder: 'Folder') -> None: #рекурсивно восстанавливает родительские ссылки для всех элементов дерева
        for child in folder._children.values():
            child._parent = folder
            if hasattr(child, '_children'):
                self._restore_parents(child)

    def __str__(self) -> str:
        return f"Disk(name='{self.name}', total={self.total_space}, free={self.free_space})"