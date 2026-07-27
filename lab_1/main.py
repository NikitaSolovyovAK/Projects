
from core.filesystem import FileSystem
from cli.command_line import CLI

def main():
    fs = FileSystem()
    if not fs.load():
        print("Сохранённое состояние не найдено. Создаю начальную конфигурацию...")
        fs._init_default_state()
        fs.save()
    cli = CLI(fs)
    cli.run()

if __name__ == "__main__":
    main()

