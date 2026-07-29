import os

from logger import logger
from models import Transaction, TransactionManager, TransactionType
from repository import JsonRepository, TransactionRepository
from stats import TransactionStats


def build_repository() -> TransactionRepository:
    storage = os.environ.get("STORAGE", "json").lower()
    if storage == "postgres":
        from postgres_repository import PostgresRepository
        logger.info("Хранилище: PostgreSQL")
        return PostgresRepository()
    logger.info("Хранилище: JSON-файл (data.json)")
    return JsonRepository("data.json")


def print_help() -> None:
    print(
        "\nКоманды:\n"
        "  add       — добавить транзакцию\n"
        "  list      — показать все транзакции\n"
        "  delete    — удалить транзакцию по id\n"
        "  stats     — показать статистику\n"
        "  save      — сохранить в хранилище\n"
        "  load      — загрузить из хранилища\n"
        "  help      — показать эту справку\n"
        "  exit      — выход\n"
    )


def cmd_add(manager: TransactionManager) -> None:
    kind = input("Тип (income/expense): ").strip().lower()
    if kind not in ("income", "expense"):
        print("Неизвестный тип. Ожидается income или expense.")
        return
    try:
        amount = int(input("Сумма: ").strip())
    except ValueError:
        print("Сумма должна быть целым числом.")
        return
    description = input("Описание: ").strip()
    category = input("Категория: ").strip()
    try:
        transaction = Transaction(amount=amount, transaction_type=TransactionType(kind), description=description, category=category)
        manager.add_transaction(transaction)
        print(f"Добавлено (id={transaction.id}).")
    except ValueError as e:
        print(f"Ошибка: {e}")


def cmd_list(manager: TransactionManager) -> None:
    transactions = manager.get_all()
    if not transactions:
        print("Транзакций пока нет.")
        return
    for t in transactions:
        sign = "+" if t.transaction_type == TransactionType.INCOME else "-"
        print(f"  id={t.id:<3} {sign}{t.amount:<8} {t.date} [{t.category or '-'}] {t.description}")


def cmd_delete(manager: TransactionManager) -> None:
    try:
        transaction_id = int(input("id для удаления: ").strip())
    except ValueError:
        print("id должен быть числом.")
        return
    try:
        manager.delete(transaction_id)
        print("Удалено.")
    except ValueError as e:
        print(f"Ошибка: {e}")


def cmd_stats(manager: TransactionManager) -> None:
    stats = TransactionStats().calculate(manager.get_all())
    print(f"  Доходы:  {stats.total_income} (записей: {stats.count_income})")
    print(f"  Расходы: {stats.total_expense} (записей: {stats.count_expense})")
    print(f"  Баланс:  {stats.balance}")
    if stats.category_expenses:
        print("  Расходы по категориям:")
        for category, amount in stats.category_expenses.items():
            print(f"    {category or '-'}: {amount}")


def main() -> None:
    manager = TransactionManager()
    repository = build_repository()
    try:
        manager.load(repository)
    except Exception as e:
        print(f"Не удалось загрузить данные: {e}")
    print("Финансовый трекер. Введите 'help' для списка команд.")
    commands = {"add": cmd_add, "list": cmd_list, "delete": cmd_delete, "stats": cmd_stats}
    while True:
        try:
            command = input("\n> ").strip().lower()
        except (EOFError, KeyboardInterrupt):
            command = "exit"
        if command == "exit":
            try:
                manager.save(repository)
                print("Данные сохранены. Выход.")
            except Exception as e:
                print(f"Ошибка при сохранении: {e}")
            break
        elif command == "help":
            print_help()
        elif command == "save":
            manager.save(repository)
            print("Сохранено.")
        elif command == "load":
            manager.load(repository)
            print("Загружено.")
        elif command in commands:
            commands[command](manager)
        elif command == "":
            continue
        else:
            print(f"Неизвестная команда: {command}. Введите 'help'.")


if __name__ == "__main__":
    main()
