import shlex
from typing import List

from operations.file_operations import touch, mkdir, write_file, cat, cp, mv, rm
from operations.permission_manager import chmod, chown, lsperm
from operations.archive_operations import archive, extract
from operations.backup_operations import backup, restore
from operations.organization import organize

from core.filesystem import FileSystem
from models.folder import Folder

class CLI:
    def __init__(self, fs: FileSystem):
        self.fs = fs
        self.commands = {
            'ls': self.do_ls,
            'cd': self.do_cd,
            'pwd': self.do_pwd,
            'tree': self.do_tree,
            'touch': self.do_touch,
            'mkdir': self.do_mkdir,
            'write': self.do_write,
            'cat': self.do_cat,
            'cp': self.do_cp,
            'mv': self.do_mv,
            'rm': self.do_rm,
            'chmod': self.do_chmod,
            'chown': self.do_chown,
            'lsperm': self.do_lsperm,
            'archive': self.do_archive,
            'extract': self.do_extract,
            'backup': self.do_backup,
            'restore': self.do_restore,
            'organize': self.do_organize,
            'help': self.do_help,
            'exit': self.do_exit,
        }

    def run(self):
        while True:
            try:
                if self.fs.current_folder:
                    prompt = self.fs.current_folder.get_path() + '> '
                else:
                    prompt = '> '
                line = input(prompt).strip()
                if not line:
                    continue
                parts = shlex.split(line)
                cmd = parts[0].lower()
                args = parts[1:]
                if cmd in self.commands:
                    self.commands[cmd](args)
                else:
                    print(f"Неизвестная команда: {cmd}. Введите 'help'.")
            except KeyboardInterrupt:
                self.fs.save()
                print("\nВыход...")
                break
            except Exception as e:
                print(f"Ошибка: {e}")

    def do_ls(self, args: List[str]):
        path = args[0] if args else '.'
        target = self.fs.resolve_path(path)
        if target is None:
            print(f"Путь '{path}' не найден")
            return
        if not isinstance(target, Folder):
            print(f"'{path}' не является папкой")
            return
        # Проверка прав на чтение
        if not target.permissions.can_read(self.fs.current_user, target):
            print("Нет прав на чтение")
            return
        for name in target.list_entries():
            entry = target.get_entry(name)
            marker = '📁' if isinstance(entry, Folder) else '📄'
            print(f"{marker} {name} ({entry.get_size()} байт)")

    def do_cd(self, args: List[str]):
        if len(args) != 1:
            print("Использование: cd <путь>")
            return
        target = self.fs.resolve_path(args[0])
        if target is None:
            print(f"Путь '{args[0]}' не найден")
            return
        if not isinstance(target, Folder):
            print(f"'{args[0]}' не является папкой")
            return
        if not target.permissions.can_execute(self.fs.current_user, target):
            print("Нет прав на доступ")
            return
        self.fs.current_folder = target

    def do_pwd(self, args: List[str]):
        """Показать текущий путь"""
        if self.fs.current_folder:
            print(self.fs.current_folder.get_path())
        else:
            print("(нет текущей папки)")

    def do_tree(self, args: List[str]):
        path = args[0] if args else '.'
        target = self.fs.resolve_path(path)
        if target is None:
            print(f"Путь '{path}' не найден")
            return
        if not isinstance(target, Folder):
            print(f"'{path}' не является папкой")
            return
        self._print_tree(target, '')

    def _print_tree(self, folder: Folder, prefix: str):
        entries = folder.list_entries()
        for i, name in enumerate(entries):
            entry = folder.get_entry(name)
            is_last = i == len(entries) - 1
            connector = '└── ' if is_last else '├── '
            print(prefix + connector + name)
            if isinstance(entry, Folder):
                extension = '    ' if is_last else '│   '
                self._print_tree(entry, prefix + extension)

    def do_touch(self, args: List[str]):
        if len(args) != 1:
            print("Использование: touch <имя>")
            return
        try:
            touch(self.fs, args[0])
            print(f"Файл '{args[0]}' создан")
        except (PermissionError, FileExistsError) as e:
            print(f"Ошибка: {e}")

    def do_mkdir(self, args: List[str]):
        if len(args) != 1:
            print("Использование: mkdir <имя>")
            return
        try:
            mkdir(self.fs, args[0])
            print(f"Папка '{args[0]}' создана")
        except (PermissionError, FileExistsError) as e:
            print(f"Ошибка: {e}")

    # ---------- Чтение/запись ----------
    def do_write(self, args: List[str]):
        if len(args) < 2:
            print("Использование: write <файл> <текст>")
            return
        file_path = args[0]
        content = ' '.join(args[1:])
        try:
            write_file(self.fs, file_path, content)
            print(f"Содержимое записано в '{file_path}'")
        except (FileNotFoundError, PermissionError) as e:
            print(f"Ошибка: {e}")

    def do_cat(self, args: List[str]):
        if len(args) != 1:
            print("Использование: cat <файл>")
            return
        try:
            content = cat(self.fs, args[0])
            print(content)
        except (FileNotFoundError, PermissionError) as e:
            print(f"Ошибка: {e}")

    def do_cp(self, args: List[str]):
        if len(args) != 2:
            print("Использование: cp <источник> <назначение>")
            return
        try:
            cp(self.fs, args[0], args[1])
            print("Скопировано")
        except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
            print(f"Ошибка: {e}")

    def do_mv(self, args: List[str]):
        if len(args) != 2:
            print("Использование: mv <источник> <назначение>")
            return
        try:
            mv(self.fs, args[0], args[1])
            print("Перемещено")
        except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
            print(f"Ошибка: {e}")

    def do_rm(self, args: List[str]):
        recursive = '-r' in args
        paths = [arg for arg in args if arg != '-r']
        if len(paths) != 1:
            print("Использование: rm [-r] <путь>")
            return
        try:
            rm(self.fs, paths[0], recursive)
            print("Удалено")
        except (FileNotFoundError, PermissionError, IsADirectoryError) as e:
            print(f"Ошибка: {e}")

    def do_chmod(self, args: List[str]):
        if len(args) != 2:
            print("Использование: chmod <режим> <путь>")
            return
        try:
            mode = int(args[0], 8)
            chmod(self.fs, args[1], mode)
            print("Права изменены")
        except ValueError:
            print("Режим должен быть восьмеричным числом (например, 755)")
        except (FileNotFoundError, PermissionError) as e:
            print(f"Ошибка: {e}")

    def do_chown(self, args: List[str]):
        if len(args) != 2:
            print("Использование: chown <имя_пользователя> <путь>")
            return
        try:
            chown(self.fs, args[1], args[0])
            print("Владелец изменён")
        except (FileNotFoundError, PermissionError, ValueError) as e:
            print(f"Ошибка: {e}")

    def do_lsperm(self, args: List[str]):
        path = args[0] if args else '.'
        entry = self.fs.resolve_path(path)
        if entry is None:
            print(f"Путь '{path}' не найден")
            return
        perms = entry.permissions
        owner = entry.owner.username if entry.owner else '?'
        print(f"Путь: {entry.get_path()}")
        print(f"Владелец: {owner}")
        print(f"Группа: {entry.group}")
        print(f"Права: {perms}")  # ожидается строка вида rwxr-xr-x
        print(f"Числовой режим: {perms.owner:o}{perms.group:o}{perms.other:o}")

    def do_archive(self, args: List[str]):
        if len(args) < 2:
            print("Использование: archive <имя_архива> <файл1> [файл2 ...]")
            return
        archive_name = args[0]
        sources = args[1:]
        try:
            archive(self.fs, sources, archive_name)
            print(f"Архив '{archive_name}' создан")
        except Exception as e:
            print(f"Ошибка при архивации: {e}")

    def do_extract(self, args: List[str]):
        if len(args) < 1 or len(args) > 2:
            print("Использование: extract <архив> [папка_назначения]")
            return
        archive_path = args[0]
        dest = args[1] if len(args) == 2 else '.'
        try:
            extract(self.fs, archive_path, dest)
            print(f"Архив распакован в '{dest}'")
        except Exception as e:
            print(f"Ошибка при распаковке: {e}")

    def do_backup(self, args: List[str]):
        name = args[0] if args else None
        try:
            backup(self.fs, name)
            print("Резервная копия создана")
        except Exception as e:
            print(f"Ошибка: {e}")

    def do_restore(self, args: List[str]):
        if len(args) != 1:
            print("Использование: restore <имя_файла>")
            return
        try:
            restore(self.fs, args[0])
            print("Резервная копия восстановлена")
        except Exception as e:
            print(f"Ошибка: {e}")

    def do_organize(self, args: List[str]):
        if len(args) != 1:
            print("Использование: organize <папка>")
            return
        try:
            organize(self.fs, args[0])
            print(f"Файлы в '{args[0]}' организованы по формату")
        except Exception as e:
            print(f"Ошибка: {e}")

    def do_help(self, args: List[str]):
        print("Доступные команды:")
        for name, method in sorted(self.commands.items()):
            doc = method.__doc__.strip() if method.__doc__ else ''
            print(f"  {name:12} {doc}")

    def do_exit(self, args: List[str]):
        self.fs.save()  # <-- добавлено
        print("Выход...")
        raise KeyboardInterrupt
