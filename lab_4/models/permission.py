from typing import Dict, Any, TYPE_CHECKING
from enum import IntFlag

if TYPE_CHECKING:
    from .user import User
    from .filesystem_entry import FileSystemEntry

class Permissions:
    class Access(IntFlag): #Определяет возможные виды доступа в виде битовых масок(позаоляет создать перечисления)
        READ = 4    # 100
        WRITE = 2   # 010
        EXECUTE = 1 # 001
        NONE = 0

    def __init__(self, owner: int = 0o7, group: int = 0o5, other: int = 0o5):
        self._owner = 0
        self._group = 0
        self._other = 0
        self.owner = owner
        self.group = group
        self.other = other

    @property
    def owner(self) -> int:
        return self._owner

    @owner.setter
    def owner(self, value: int):
        if not 0 <= value <= 7:
            raise ValueError("Права владельца должны быть в диапазоне 0..7")
        self._owner = value

    @property
    def group(self) -> int:
        return self._group

    @group.setter
    def group(self, value: int):
        if not 0 <= value <= 7:
            raise ValueError("Права группы должны быть в диапазоне 0..7")
        self._group = value

    @property
    def other(self) -> int:
        return self._other

    @other.setter
    def other(self, value: int):
        if not 0 <= value <= 7:
            raise ValueError("Права остальных должны быть в диапазоне 0..7")
        self._other = value

    #Определяет какая категория прав применяется к данному пользователю
    def _get_rights_for_user(self, user: 'User', entry: 'FileSystemEntry') -> int:
        if user.user_id == entry.owner.user_id:
            return self._owner
        elif entry.group in user.groups:
            return self._group
        else:
            return self._other

    def can_read(self, user: 'User', entry: 'FileSystemEntry') -> bool:
        rights = self._get_rights_for_user(user, entry)
        return bool(rights & self.Access.READ)

    def can_write(self, user: 'User', entry: 'FileSystemEntry') -> bool:
        rights = self._get_rights_for_user(user, entry)
        return bool(rights & self.Access.WRITE)

    def can_execute(self, user: 'User', entry: 'FileSystemEntry') -> bool:
        rights = self._get_rights_for_user(user, entry)
        return bool(rights & self.Access.EXECUTE)

    def to_dict(self) -> Dict[str, int]:
        return {
            "owner": self._owner,
            "group": self._group,
            "other": self._other
        }

    #Восстановление объекта Permission из словаря
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'Permissions':
        return cls(
            owner=data.get("owner", 6),
            group=data.get("group", 4),
            other=data.get("other", 0)
        )

    def __str__(self) -> str:
        def _fmt(r: int) -> str:
            read = 'r' if r & self.Access.READ else '-'
            write = 'w' if r & self.Access.WRITE else '-'
            execute = 'x' if r & self.Access.EXECUTE else '-'
            return read + write + execute
        return f"{_fmt(self._owner)}{_fmt(self._group)}{_fmt(self._other)}"

    def __repr__(self) -> str:
        return f"Permissions(owner={self._owner:o}, group={self._group:o}, other={self._other:o})"