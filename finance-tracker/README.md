# Finance Tracker

Приложение для учёта личных финансов (доходы и расходы). Есть веб-интерфейс на FastAPI и консольный интерфейс (CLI). Оба используют общий код — модель, статистику и слой хранения.

## Возможности

- Учёт доходов и расходов
- Веб-интерфейс: баланс, добавление операций, список, удаление
- Статистика: суммы, баланс, средние, расходы по категориям
- Хранение в JSON-файле или в PostgreSQL (взаимозаменяемо)
- REST API и консольный интерфейс

## Структура проекта

```
finance-tracker/
├── models.py               # Transaction и TransactionManager
├── stats.py                # Расчёт статистики
├── decorators.py           # Декораторы логирования и замера времени
├── context_managers.py     # Пакетное добавление транзакций
├── logger.py               # Настройка логирования
├── repository.py           # Абстрактное хранилище + JsonRepository
├── postgres_repository.py  # Хранилище на PostgreSQL
├── db_connect.py           # Проверка подключения к PostgreSQL
├── main.py                 # Консольный интерфейс (CLI)
├── app.py                  # Веб-API на FastAPI
├── static/
│   └── index.html          # Веб-интерфейс
├── data.json               # Пример данных
├── requirements.txt
├── .env.example
└── .gitignore
```

## Установка

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Запуск веб-интерфейса

```bash
uvicorn app:app --reload
```

Откройте в браузере `http://127.0.0.1:8000` — веб-интерфейс.
Документация API (Swagger): `http://127.0.0.1:8000/docs`.

### Эндпоинты

| Метод  | Путь                        | Описание |
|--------|-----------------------------|----------|
| GET    | `/api/transactions`         | Список всех операций |
| POST   | `/api/transactions`         | Создать операцию |
| GET    | `/api/transactions/{id}`    | Получить операцию по id |
| DELETE | `/api/transactions/{id}`    | Удалить операцию |
| GET    | `/api/stats`                | Статистика |

## Запуск консольного интерфейса

```bash
python main.py
```

Команды: `add`, `list`, `delete`, `stats`, `save`, `load`, `help`, `exit`.

## Хранилище PostgreSQL

По умолчанию данные хранятся в `data.json`. Для PostgreSQL в CLI задайте переменные окружения (Windows PowerShell):

```powershell
$env:STORAGE="postgres"
$env:DB_PASSWORD="ваш_пароль"
python main.py
```

База с именем из `DB_NAME` должна быть создана заранее; таблицу приложение создаёт само.
