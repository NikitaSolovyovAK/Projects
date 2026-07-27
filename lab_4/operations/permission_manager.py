from core.filesystem import FileSystem


def chmod(fs: FileSystem, path: str, mode: int) -> None:
    """Изменить права доступа (восьмеричное число, например 0o755)."""
    entry = fs.resolve_path(path)
    if entry is None:
        raise FileNotFoundError(f"Путь '{path}' не найден")
    if entry.owner.user_id != fs.current_user.user_id and fs.current_user.username != 'admin':
        raise PermissionError("Только владелец или admin может менять права")
    owner_mode = (mode >> 6) & 0o7
    group_mode = (mode >> 3) & 0o7
    other_mode = mode & 0o7
    entry.permissions.owner = owner_mode
    entry.permissions.group = group_mode
    entry.permissions.other = other_mode


def chown(fs: FileSystem, path: str, new_owner_name: str) -> None:
    """Сменить владельца (только admin)."""
    if fs.current_user.username != 'admin':
        raise PermissionError("Только admin может менять владельца")
    new_owner = None
    for user in fs.users.values():
        if user.username == new_owner_name:
            new_owner = user
            break
    if new_owner is None:
        raise ValueError(f"Пользователь '{new_owner_name}' не найден")
    entry = fs.resolve_path(path)
    if entry is None:
        raise FileNotFoundError(f"Путь '{path}' не найден")
    entry.owner = new_owner


def lsperm(fs: FileSystem, path: str) -> str:
    """Вернуть строку с информацией о правах (используется в CLI)."""
    entry = fs.resolve_path(path)
    if entry is None:
        raise FileNotFoundError(f"Путь '{path}' не найден")
    perms = entry.permissions
    owner = entry.owner.username if entry.owner else '?'
    result = f"Путь: {entry.get_path()}\n"
    result += f"Владелец: {owner}\n"
    result += f"Группа: {entry.group}\n"
    result += f"Права: {perms}\n"
    result += f"Числовой режим: {perms.owner:o}{perms.group:o}{perms.other:o}"
    return result
