import json
import os
from typing import Dict, List, Optional, Union

from models.user import User
from models.disk import Disk
from models.folder import Folder
from models.filesystem_entry import FileSystemEntry


class FileSystem:

    def __init__(self, state_file: str = 'data/state.json'):
        self.state_file = state_file
        self.users: Dict[str, User] = {}
        self.disks: List[Disk] = []
        self.current_user: Optional[User] = None
        self.current_disk: Optional[Disk] = None
        self.current_folder: Optional[Folder] = None

    def load(self) -> bool:
        if not os.path.exists(self.state_file):
            return False

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            return False

        users_data = data.get('users', {})
        for user_id, user_dict in users_data.items():
            user = User.from_dict(user_dict)
            self.users[user_id] = user

        disks_data = data.get('disks', [])
        for disk_dict in disks_data:
            disk = Disk.from_dict(disk_dict, self.users)
            self.disks.append(disk)

        current_user_id = data.get('current_user_id')
        if current_user_id and current_user_id in self.users:
            self.current_user = self.users[current_user_id]

        current_disk_id = data.get('current_disk_id')
        if current_disk_id:
            for disk in self.disks:
                if disk.disk_id == current_disk_id:
                    self.current_disk = disk
                    break

        current_path = data.get('current_path', '/')
        if self.current_disk and self.current_disk.root:
            self.current_folder = self.resolve_path(current_path, self.current_disk.root)
            if self.current_folder is None:
                self.current_folder = self.current_disk.root  # fallback на корень

        return True

    def save(self) -> None:
        # Создаём директорию, если её нет
        os.makedirs(os.path.dirname(self.state_file), exist_ok=True)

        data = {
            'users': {uid: user.to_dict() for uid, user in self.users.items()},
            'disks': [disk.to_dict() for disk in self.disks],
            'current_user_id': self.current_user.user_id if self.current_user else None,
            'current_disk_id': self.current_disk.disk_id if self.current_disk else None,
            'current_path': self.current_folder.get_path() if self.current_folder else '/'
        }

        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def resolve_path(self, path: str, base: Optional[Folder] = None) -> Optional[FileSystemEntry]:
        if not self.current_disk:
            raise RuntimeError("Нет текущего диска")

        if base is None:
            base = self.current_folder
        if base is None:
            base = self.current_disk.root

        return self.current_disk.resolve_path(path, base)

    def _init_default_state(self) -> None:
        # Создаём администратора
        admin = User("admin")
        self.users[admin.user_id] = admin
        self.current_user = admin

        disk = Disk(name="C:", total_space=1024 * 1024 * 1024)  # 1 ГБ
        disk.format(admin)
        self.disks.append(disk)
        self.current_disk = disk
        self.current_folder = disk.root
