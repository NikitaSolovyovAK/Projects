import sys
from core.filesystem import FileSystem


def main():
    fs = FileSystem()
    if not fs.load():
        print("Сохранённое состояние не найдено. Создаю начальную конфигурацию...")
        fs._init_default_state()
        fs.save()

    mode = 'cli'
    if '--web' in sys.argv:
        mode = 'web'
    elif '--cli' in sys.argv:
        mode = 'cli'

    if mode == 'web':
        from web.app import create_app
        app = create_app(fs)
        port = 5000
        for arg in sys.argv:
            if arg.startswith('--port='):
                port = int(arg.split('=')[1])
        print(f"Запуск веб-сервера на http://127.0.0.1:{port}")
        app.run(debug=True, port=port)
    else:
        from cli.command_line import CLI
        cli = CLI(fs)
        cli.run()


if __name__ == "__main__":
    main()
