from flask import Flask, render_template, request, jsonify
from core.filesystem import FileSystem
from models.folder import Folder
from models.file import File
from operations.file_operations import touch, mkdir, write_file, cat, cp, mv, rm
from operations.permission_manager import chmod, chown
from operations.archive_operations import archive, extract
from operations.backup_operations import backup, restore
from operations.organization import organize


def create_app(fs: FileSystem) -> Flask:
    app = Flask(
        __name__,
        template_folder='templates',
        static_folder='static'
    )

    def _build_tree(folder: Folder) -> list:
        items = []
        for name in folder.list_entries():
            entry = folder.get_entry(name)
            is_folder = isinstance(entry, Folder)
            node = {
                'name': name,
                'path': entry.get_path(),
                'is_folder': is_folder,
                'size': entry.get_size(),
                'owner': entry.owner.username if entry.owner else '?',
                'permissions': str(entry.permissions),
                'modified': entry.modified_at.strftime('%Y-%m-%d %H:%M'),
            }
            if is_folder:
                node['children'] = _build_tree(entry)
            else:
                node['format'] = entry.format.name if hasattr(entry, 'format') else ''
            items.append(node)
        return items

    def _ls(folder: Folder) -> list:
        items = []
        for name in folder.list_entries():
            entry = folder.get_entry(name)
            is_folder = isinstance(entry, Folder)
            items.append({
                'name': name,
                'path': entry.get_path(),
                'is_folder': is_folder,
                'size': entry.get_size(),
                'owner': entry.owner.username if entry.owner else '?',
                'group': entry.group,
                'permissions': str(entry.permissions),
                'perm_numeric': f"{entry.permissions.owner:o}{entry.permissions.group:o}{entry.permissions.other:o}",
                'modified': entry.modified_at.strftime('%Y-%m-%d %H:%M'),
                'format': entry.format.name if hasattr(entry, 'format') and not is_folder else '',
            })
        return items

    def _ok(message, **extra):
        return jsonify({'status': 'ok', 'message': message, **extra})#jsonify() функция Flask превращает словарь в HTTP ответ с JSON

    def _err(message, code=400):
        return jsonify({'status': 'error', 'message': message}), code

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/api/state')#декоратор, когда браузер отправляет GET на адрес '/api/state', Flask вызывает функцию api_state()
    def api_state():
        current_path = fs.current_folder.get_path() if fs.current_folder else '/'
        entries = _ls(fs.current_folder) if fs.current_folder else []
        disk_info = None
        if fs.current_disk:
            fs.current_disk.update_free_space()
            disk_info = {
                'name': fs.current_disk.name,
                'total': fs.current_disk.total_space,
                'free': fs.current_disk.free_space,
                'used': fs.current_disk.total_space - fs.current_disk.free_space,
                'filesystem': fs.current_disk.filesystem,
            }
        tree = _build_tree(fs.current_disk.root) if fs.current_disk else []
        return jsonify({
            'current_path': current_path,
            'current_user': fs.current_user.username if fs.current_user else '?',
            'entries': entries,
            'disk': disk_info,
            'tree': tree,
        })

    @app.route('/api/cd', methods=['POST'])
    def api_cd():
        path = request.json.get('path', '')
        try:
            target = fs.resolve_path(path)
            if target is None:
                return _err(f"Путь '{path}' не найден")
            if not isinstance(target, Folder):
                return _err(f"'{path}' не является папкой")
            fs.current_folder = target
            fs.save()
            return _ok(f"Перешли в {target.get_path()}")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/touch', methods=['POST'])
    def api_touch():
        name = request.json.get('name', '')
        if not name:
            return _err("Укажите имя файла")
        try:
            touch(fs, name)
            fs.save()
            return _ok(f"Файл '{name}' создан")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/mkdir', methods=['POST'])
    def api_mkdir():
        name = request.json.get('name', '')
        if not name:
            return _err("Укажите имя папки")
        try:
            mkdir(fs, name)
            fs.save()
            return _ok(f"Папка '{name}' создана")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/write', methods=['POST'])
    def api_write():
        path = request.json.get('path', '')
        content = request.json.get('content', '')
        if not path:
            return _err("Укажите путь к файлу")
        try:
            write_file(fs, path, content)
            fs.save()
            return _ok(f"Содержимое записано в '{path}'")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/cat', methods=['POST'])
    def api_cat():
        path = request.json.get('path', '')
        if not path:
            return _err("Укажите путь к файлу")
        try:
            content = cat(fs, path)
            return _ok("OK", content=content)
        except Exception as e:
            return _err(str(e))

    @app.route('/api/cp', methods=['POST'])
    def api_cp():
        src = request.json.get('src', '')
        dst = request.json.get('dst', '')
        if not src or not dst:
            return _err("Укажите источник и назначение")
        try:
            cp(fs, src, dst)
            fs.save()
            return _ok(f"Скопировано '{src}' -> '{dst}'")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/mv', methods=['POST'])
    def api_mv():
        src = request.json.get('src', '')
        dst = request.json.get('dst', '')
        if not src or not dst:
            return _err("Укажите источник и назначение")
        try:
            mv(fs, src, dst)
            fs.save()
            return _ok(f"Перемещено '{src}' -> '{dst}'")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/rm', methods=['POST'])
    def api_rm():
        path = request.json.get('path', '')
        recursive = request.json.get('recursive', False)
        if not path:
            return _err("Укажите путь")
        try:
            rm(fs, path, recursive)
            fs.save()
            return _ok(f"Удалено '{path}'")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/chmod', methods=['POST'])
    def api_chmod():
        path = request.json.get('path', '')
        mode = request.json.get('mode', '')
        if not path or not mode:
            return _err("Укажите путь и режим")
        try:
            mode_int = int(mode, 8)
            chmod(fs, path, mode_int)
            fs.save()
            return _ok(f"Права для '{path}' изменены на {mode}")
        except ValueError:
            return _err("Режим должен быть восьмеричным числом (например, 755)")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/chown', methods=['POST'])
    def api_chown():
        path = request.json.get('path', '')
        owner = request.json.get('owner', '')
        if not path or not owner:
            return _err("Укажите путь и владельца")
        try:
            chown(fs, path, owner)
            fs.save()
            return _ok(f"Владелец '{path}' изменён на '{owner}'")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/archive', methods=['POST'])
    def api_archive():
        name = request.json.get('name', '')
        sources = request.json.get('sources', [])
        if not name or not sources:
            return _err("Укажите имя архива и файлы")
        try:
            archive(fs, sources, name)
            fs.save()
            return _ok(f"Архив '{name}' создан")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/extract', methods=['POST'])
    def api_extract():
        path = request.json.get('path', '')
        destination = request.json.get('destination', '.')
        if not path:
            return _err("Укажите путь к архиву")
        try:
            extract(fs, path, destination)
            fs.save()
            return _ok(f"Архив '{path}' распакован")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/backup', methods=['POST'])
    def api_backup():
        name = request.json.get('name', None)
        try:
            backup(fs, name)
            fs.save()
            return _ok("Резервная копия создана")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/restore', methods=['POST'])
    def api_restore():
        name = request.json.get('name', '')
        if not name:
            return _err("Укажите имя резервной копии")
        try:
            restore(fs, name)
            fs.save()
            return _ok(f"Восстановлено из '{name}'")
        except Exception as e:
            return _err(str(e))

    @app.route('/api/organize', methods=['POST'])
    def api_organize():
        path = request.json.get('path', '')
        if not path:
            return _err("Укажите путь к папке")
        try:
            organize(fs, path)
            fs.save()
            return _ok(f"Файлы в '{path}' организованы")
        except Exception as e:
            return _err(str(e))

    return app
