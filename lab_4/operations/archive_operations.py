import zipfile
import io
from typing import List
from core.filesystem import FileSystem
from models.file import File
from models.folder import Folder
from models.file_format import FileFormat


def archive(fs: FileSystem, sources: List[str], archive_name: str) -> File:
    if fs.current_folder is None:
        raise RuntimeError("Нет текущей папки")
    if not fs.current_folder.permissions.can_write(fs.current_user, fs.current_folder):
        raise PermissionError("Нет прав на запись в текущей папке")

    files_to_archive = []
    for src in sources:
        entry = fs.resolve_path(src)
        if entry is None:
            raise FileNotFoundError(f"Источник '{src}' не найден")
        if not isinstance(entry, File):
            raise IsADirectoryError(f"'{src}' не является файлом")
        if not entry.permissions.can_read(fs.current_user, entry):
            raise PermissionError(f"Нет прав на чтение '{src}'")
        files_to_archive.append(entry)

    zip_buffer = io.BytesIO()#Создает буфер в памяти который ведет себя как файл но данные храняться в оперативной памяти
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf: #Открытие файла для записи в буфер
        for file_entry in files_to_archive:
            zf.writestr(file_entry.name, file_entry.content)

    archive_file = File(
        name=archive_name,
        owner=fs.current_user,
        file_format=FileFormat.ZIP,
        content=zip_buffer.getvalue()
    )
    fs.current_folder.add_entry(archive_file)
    return archive_file


def extract(fs: FileSystem, archive_path: str, destination: str) -> None:
    archive_entry = fs.resolve_path(archive_path)
    if archive_entry is None:
        raise FileNotFoundError(f"Архив '{archive_path}' не найден")
    if not isinstance(archive_entry, File):
        raise ValueError(f"'{archive_path}' не является файлом")
    if archive_entry.format != FileFormat.ZIP:
        raise ValueError(f"Файл '{archive_path}' не ZIP-архив")

    dest_folder = fs.resolve_path(destination)
    if dest_folder is None or not isinstance(dest_folder, Folder):
        raise NotADirectoryError(f"Папка назначения '{destination}' не найдена или не является папкой")
    if not dest_folder.permissions.can_write(fs.current_user, dest_folder):
        raise PermissionError(f"Нет прав на запись в папку '{destination}'")

    zip_data = archive_entry.content#извлекает содержимое архивного файла
    with zipfile.ZipFile(io.BytesIO(zip_data), 'r') as zf: #Создает объект BytesIO из байтов архива и открвает его как zip файл
        for zip_info in zf.infolist():
            if zip_info.filename.endswith('/'):
                continue  # пропускаем директории
            content = zf.read(zip_info.filename)#читает содержимое файла из архива по его имени возвращает байты
            filename = zip_info.filename.split('/')[-1]  # берём только имя файла
            file_format = FileFormat.from_file(filename) or FileFormat.TXT
            new_file = File(filename, fs.current_user, file_format, content=content)
            dest_folder.add_entry(new_file)

