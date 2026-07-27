from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional, Dict, Any, TYPE_CHECKING

if TYPE_CHECKING:
    from .user import User
    from .permission import Permissions
    from .folder import Folder
    from .disk import Disk

class FileSystemEntry(ABC):#определяет общие атрибуты и поведение для всех элементов файловой системы

    def __init__(self, name: str, owner: 'User', group: str = "users", permissions: Optional['Permissions'] = None) -> None:
        self._name = name
        self._group = group
        self._owner = owner

        if permissions is None:
            from .permission import Permissions
            permissions = Permissions()

        self._permissions = permissions
        self._created_at = datetime.now()
        self._modified_at = self._created_at
        self._parent: Optional['Folder'] = None  # ссылка на родительскую папку

    @property
    def name(self) -> str:
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._name = value
        self._update_modified()

    @property
    def owner(self) -> 'User':
        return self._owner

    @owner.setter
    def owner(self, value: 'User') -> None:
        self._owner = value
        self._update_modified()

    @property
    def group(self) -> str:
        return self._group

    @group.setter
    def group(self, value: str) -> None:
        self._group = value
        self._update_modified()

    @property
    def permissions(self) -> 'Permissions':
        return self._permissions

    @permissions.setter
    def permissions(self, value: 'Permissions') -> None:
        self._permissions = value
        self._update_modified()

    @property
    def created_at(self) -> datetime:
        return self._created_at

    @property
    def modified_at(self) -> datetime:
        return self._modified_at

    #Возвращает ссылку на родительскую папку
    @property
    def parent(self) -> Optional['Folder']:
        return self._parent

    #Метод ищет диск к которому принадлежит данный элемент
    @property
    def disk(self) -> Optional['Disk']:
        if hasattr(self, '_disk') and self._disk is not None:
            return self._disk
        if self._parent is not None:
            return self._parent.disk
        return None

    #строит абсолютный путь от корня до диска
    def get_path(self) -> str:
        if self._parent is None:
            return '/'
        parts = []
        current = self
        while current._parent is not None:
            parts.append(current.name)
            current = current._parent
        root_name = current.name
        if root_name and root_name != '/':
            parts.append(root_name)
        return '/' + '/'.join(reversed(parts))

    def _update_modified(self) -> None:
        self._modified_at = datetime.now()

    @abstractmethod
    def get_size(self) -> int:
        pass

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self._name,
            "owner": self._owner.user_id,
            "group": self._group,
            "permissions": self._permissions.to_dict(),
            "created_at": self._created_at.isoformat(),
            "modified_at": self._modified_at.isoformat()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], users_map: Dict[str, 'User']) -> 'FileSystemEntry':
        raise NotImplementedError("Метод from_dict должен быть реализован в подклассе")