from models.file import File
from models.folder import Folder
from models.file_format import FileFormat
from core.filesystem import FileSystem


def touch(fs: FileSystem, filename: str) -> File:
    """Создать пустой файл в текущей папке."""
    if fs.current_folder is None:
        raise RuntimeError("Нет текущей папки")
    if not fs.current_folder.permissions.can_write(fs.current_user, fs.current_folder):
        raise PermissionError("Нет прав на запись в текущей папке")
    if filename in fs.current_folder.list_entries():
        raise FileExistsError(f"Файл '{filename}' уже существует")
    file_format = FileFormat.from_file(filename) or FileFormat.TXT
    new_file = File(filename, fs.current_user, file_format, content=b"")
    fs.current_folder.add_entry(new_file)
    return new_file


def mkdir(fs: FileSystem, dirname: str) -> Folder:
    """Создать новую папку в текущей папке."""
    if fs.current_folder is None:
        raise RuntimeError("Нет текущей папки")
    if not fs.current_folder.permissions.can_write(fs.current_user, fs.current_folder):
        raise PermissionError("Нет прав на запись в текущей папке")
    if dirname in fs.current_folder.list_entries():
        raise FileExistsError(f"Папка '{dirname}' уже существует")
    new_folder = Folder(dirname, fs.current_user)
    fs.current_folder.add_entry(new_folder)
    return new_folder


def write_file(fs: FileSystem, file_path: str, content: str) -> None:
    """Записать текст в файл."""
    entry = fs.resolve_path(file_path)
    if entry is None:
        raise FileNotFoundError(f"Файл '{file_path}' не найден")
    if not isinstance(entry, File):
        raise IsADirectoryError(f"'{file_path}' не является файлом")
    if not entry.permissions.can_write(fs.current_user, entry):
        raise PermissionError(f"Нет прав на запись в '{file_path}'")
    entry.content = content.encode('utf-8')


def cat(fs: FileSystem, file_path: str) -> str:
    """Прочитать содержимое файла."""
    entry = fs.resolve_path(file_path)
    if entry is None:
        raise FileNotFoundError(f"Файл '{file_path}' не найден")
    if not isinstance(entry, File):
        raise IsADirectoryError(f"'{file_path}' не является файлом")
    if not entry.permissions.can_read(fs.current_user, entry):
        raise PermissionError(f"Нет прав на чтение '{file_path}'")
    return entry.content.decode('utf-8')


def cp(fs: FileSystem, src: str, dst: str) -> File:
    source = fs.resolve_path(src)
    if source is None:
        raise FileNotFoundError(f"Исходный файл '{src}' не найден")
    if not isinstance(source, File):
        raise IsADirectoryError(f"'{src}' не является файлом")
    if not source.permissions.can_read(fs.current_user, source):
        raise PermissionError(f"Нет прав на чтение '{src}'")

    # Определяем целевую папку и имя
    dest_target = fs.resolve_path(dst)
    if dest_target is not None and isinstance(dest_target, Folder):
        # Если dst указывает на существующую папку, копируем внутрь с исходным именем
        dest_folder = dest_target
        new_name = source.name
    else:
        #Если dst не является существующей папкой, то считаем что dst - содержит полный путь с именем файла, либо просто новое имя
        if '/' in dst:
            parts = dst.rsplit('/', 1)
            dest_folder_path = parts[0] if parts[0] else '/'
            new_name = parts[1]
        else:# целевая папка - текущая папка, а dst - новое имя
            dest_folder_path = '.'
            new_name = dst
        dest_folder = fs.resolve_path(dest_folder_path)
        if dest_folder is None or not isinstance(dest_folder, Folder):
            raise NotADirectoryError(f"Целевая папка '{dest_folder_path}' не найдена или не является папкой")

    if not dest_folder.permissions.can_write(fs.current_user, dest_folder):
        raise PermissionError(f"Нет прав на запись в папку '{dest_folder.get_path()}'")
    if new_name in dest_folder.list_entries():
        raise FileExistsError(f"Файл '{new_name}' уже существует в целевой папке")

    # Создаём копию файла
    new_file = File(
        name=new_name,
        owner=fs.current_user,
        file_format=source.format,
        content=source.content  # копируем байты
    )
    dest_folder.add_entry(new_file)
    return new_file


def mv(fs: FileSystem, src: str, dst: str) -> File:
    """Переместить/переименовать файл (копирует + удаляет исходный)."""
    copied = cp(fs, src, dst)
    source = fs.resolve_path(src)
    source.parent.remove_entry(source.name)
    return copied


def rm(fs: FileSystem, path: str, recursive: bool = False) -> None:
    target = fs.resolve_path(path)
    if target is None:
        raise FileNotFoundError(f"Путь '{path}' не найден")
    if target.parent is None:
        raise PermissionError("Нельзя удалить корневую папку")
    if not target.parent.permissions.can_write(fs.current_user, target.parent):
        raise PermissionError(f"Нет прав на удаление из папки '{target.parent.get_path()}'")

    if isinstance(target, Folder):
        if not recursive and target.list_entries():
            raise IsADirectoryError(f"Папка '{path}' не пуста. Используйте rm -r для рекурсивного удаления")
    target.parent.remove_entry(target.name)