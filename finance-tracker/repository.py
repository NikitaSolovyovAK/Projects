import json
from abc import ABC, abstractmethod

from decorators import timed
from logger import logger
from models import Transaction


class TransactionRepository(ABC):
    @abstractmethod
    def save(self, transactions: list[Transaction]) -> None:
        ...

    @abstractmethod
    def load(self) -> list[Transaction]:
        ...


class JsonRepository(TransactionRepository):
    def __init__(self, filepath: str) -> None:
        self.filepath = filepath

    @timed
    def save(self, transactions: list[Transaction]) -> None:
        try:
            data = [t.to_dict() for t in transactions]
            with open(self.filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Сохранено {len(transactions)} транзакций в файл '{self.filepath}'")
        except Exception as e:
            logger.error(f"Ошибка при сохранении в файл '{self.filepath}': {e}")
            raise

    @timed
    def load(self) -> list[Transaction]:
        try:
            with open(self.filepath, 'r', encoding='utf-8') as file:
                content = json.load(file)
            transactions = [Transaction.from_dict(item) for item in content]
            logger.info(f"Загружено {len(transactions)} транзакций из файла '{self.filepath}'")
            return transactions
        except FileNotFoundError:
            logger.warning(f"Файл не найден '{self.filepath}', возвращаю пустой список")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка формата JSON в файле '{self.filepath}': {e}")
            raise
        except Exception as e:
            logger.error(f"Ошибка загрузки из файла '{self.filepath}': {e}")
            raise
