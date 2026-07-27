from core.filesystem import FileSystem
from models.folder import Folder


def organize(fs: FileSystem, folder_path: str) -> None:
    folder = fs.resolve_path(folder_path)
    if folder is None or not isinstance(folder, Folder):
        raise NotADirectoryError(f"'{folder_path}' не является папкой или не существует")
    if not folder.permissions.can_write(fs.current_user, folder):
        raise PermissionError(f"Нет прав на изменение содержимого папки '{folder_path}'")

    # Получаем все файлы в папке через новый метод
    files = folder.get_files()

    for file_entry in files:
        cat_name = file_entry.format.get_folder_name_for_category()
        if cat_name not in folder.list_entries():
            cat_folder = Folder(cat_name, fs.current_user)
            folder.add_entry(cat_folder)
        else:
            cat_folder = folder.get_entry(cat_name)
            if not isinstance(cat_folder, Folder):
                # Если существует файл с таким именем, пропускаем (или можно выбросить ошибку)
                continue
        # Перемещаем файл
        folder.remove_entry(file_entry.name)
        cat_folder.add_entry(file_entry)