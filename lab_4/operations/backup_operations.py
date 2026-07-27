import json
import datetime
from typing import Optional
from core.filesystem import FileSystem
from models.file import File
from models.folder import Folder
from models.file_format import FileFormat


def backup(fs: FileSystem, name: Optional[str] = None) -> File:
    if fs.current_disk is None:
        raise RuntimeError("Нет текущего диска")
    root = fs.current_disk.root
    if 'backups' not in root.list_entries():
        backups_folder = Folder('backups', fs.current_user)
        root.add_entry(backups_folder)
    else:
        backups_folder = root.get_entry('backups')
        if not isinstance(backups_folder, Folder):
            raise NotADirectoryError("'backups' не является папкой")

    if name is None:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        name = f"backup_{timestamp}.json"
    elif not name.endswith('.json'):
        name += '.json'
    disk_data = fs.current_disk.to_dict()#рекурсивно сериализует весь диск
    backup_content = json.dumps(disk_data, indent=2, ensure_ascii=False).encode('utf-8')

    backup_file = File(name, fs.current_user, FileFormat.JSON, content=backup_content)
    backups_folder.add_entry(backup_file)
    return backup_file


def restore(fs: FileSystem, backup_name: str) -> None:
    if fs.current_disk is None:
        raise RuntimeError("Нет текущего диска")
    root = fs.current_disk.root
    if 'backups' not in root.list_entries():
        raise FileNotFoundError("Папка backups не найдена")
    backups_folder = root.get_entry('backups')
    if not isinstance(backups_folder, Folder):
        raise NotADirectoryError("'backups' не является папкой")
    if backup_name not in backups_folder.list_entries():
        raise FileNotFoundError(f"Резервная копия '{backup_name}' не найдена")
    backup_entry = backups_folder.get_entry(backup_name)
    if not isinstance(backup_entry, File):
        raise ValueError(f"'{backup_name}' не является файлом")

    try:
        data = json.loads(backup_entry.content.decode('utf-8'))
    except json.JSONDecodeError:
        raise ValueError("Файл резервной копии повреждён")

    from models.disk import Disk
    new_disk = Disk.from_dict(data, fs.users)
    for i, disk in enumerate(fs.disks):
        if disk.disk_id == fs.current_disk.disk_id:#назначает новый диск на замену старому + корневую папку меняет
            fs.disks[i] = new_disk
            fs.current_disk = new_disk
            fs.current_folder = new_disk.root
            break
    else:
        fs.disks.append(new_disk)
        fs.current_disk = new_disk
        fs.current_folder = new_disk.root
