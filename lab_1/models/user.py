from datetime import datetime
from typing import Dict, Any, TYPE_CHECKING, Optional
import uuid

if TYPE_CHECKING:
    from .folder import Folder

class User:
    """Определение полей пользователя"""
    def __init__(self, username: str):
        self.username = username
        self.user_id = str(uuid.uuid4())[:8]
        self.created_at = datetime.now()
        self.home_directory = None
        self.current_directory = None
        self.home_path: Optional[str] = None
        self.current_path: Optional[str] = None
        self.groups = ["users"]
        self.permissions = {
            "read_own_files": True,
            "write_own_files": True,
            "delete_own_files": True,
            "create_files": True,
            "create_folders": True,
        }

    def __str__(self) -> str:
        return f"User(username='{self.username}', id='{self.user_id}')"

    def __repr__(self) -> str:
        return f"User(username={self.username!r}, id={self.user_id}, created_at={self.created_at!r})"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "username": self.username,
            "user_id": self.user_id,
            "created_at": self.created_at.isoformat(),
            "groups": self.groups,
            "permissions": self.permissions,
        }

    #Восстановление объекта класса User из словаря
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'User':
        user = cls(data["username"])
        user.user_id = data.get("user_id", user.user_id)
        created_at_str = data.get("created_at")
        if created_at_str:
            user.created_at = datetime.fromisoformat(created_at_str)
        user.groups = data.get("groups", ["users"])
        user.permissions = data.get("permissions", {})
        user.home_path = data.get("home_path")
        user.current_path = data.get("current_path")
        return user

    def set_home(self, folder: 'Folder') -> None:
        self.home_directory = folder
        self.home_path = folder.get_path() if folder else None

    def set_current_directory(self, folder: 'Folder') -> None:
        self.current_directory = folder
        self.current_path = folder.get_path() if folder else None

    def add_to_group(self, group: str) -> None:
        if group not in self.groups:
            self.groups.append(group)

    def remove_from_group(self, group: str) -> None:
        if group in self.groups:
            self.groups.remove(group)

    #установлениие значения для конкретного глобально права
    def set_permission(self, permission: str, value: bool) -> None:
        self.permissions[permission] = value

    def is_in_group(self, group: str) -> bool:
        return group in self.groups