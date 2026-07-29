from datetime import date
from enum import Enum
from typing import Dict, Any, TYPE_CHECKING
from logger import logger
from decorators import log_action

if TYPE_CHECKING:
    from repository import TransactionRepository


class TransactionType(Enum):
    INCOME = "income"
    EXPENSE = "expense"


class Transaction:
    _counter: int = 0

    def __init__(self, amount: int, transaction_type: TransactionType, transaction_date: date | None = None, description: str = "", category: str = "") -> None:
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
        Transaction._counter += 1
        self.id = Transaction._counter
        self.amount = amount
        self.date = transaction_date if transaction_date is not None else date.today()
        self.description = description
        self.category = category
        self.transaction_type = transaction_type

    def __repr__(self) -> str:
        return (f"Transaction(id={self.id}, amount={self.amount}, "
                f"date={self.date}, description='{self.description}', "
                f"type={self.transaction_type}, category='{self.category}')")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "amount": self.amount,
            "date": self.date.isoformat(),
            "description": self.description,
            "category": self.category,
            "transaction_type": self.transaction_type.value,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Transaction':
        obj = cls(
            amount=data["amount"],
            transaction_type=TransactionType(data["transaction_type"]),
            transaction_date=date.fromisoformat(data["date"]),
            description=data.get("description", ''),
            category=data.get("category", ''),
        )
        obj.id = data["id"]
        return obj


class TransactionManager:

    class TransactionManagerIterator:
        def __init__(self, transactions: list[Transaction], start: int = 0):
            self._index = start
            self._transactions = transactions

        def __next__(self):
            if self._index >= len(self._transactions):
                raise StopIteration
            val = self._transactions[self._index]
            self._index += 1
            return val

    def __init__(self, start: int = 0):
        self._transactions: list[Transaction] = []
        self._index = start

    def __iter__(self):
        return self.TransactionManagerIterator(self._transactions, self._index)

    def filter_by_type(self, transaction_type: TransactionType):
        for t in self._transactions:
            if t.transaction_type == transaction_type:
                yield t

    def filter_by_date_range(self, start_date: date, end_date: date):
        for t in self._transactions:
            if start_date <= t.date <= end_date:
                yield t

    @log_action
    def add_transaction(self, transaction: Transaction) -> None:
        self._transactions.append(transaction)
        logger.info(f"Добавлена транзакция {transaction}")

    def get_all(self) -> list[Transaction]:
        return self._transactions.copy()

    @log_action
    def get_by_id(self, transaction_id: int) -> Transaction | None:
        for transaction in self._transactions:
            if transaction_id == transaction.id:
                logger.info(f"Получена транзакция - {transaction} по id {transaction_id}")
                return transaction
        return None

    @log_action
    def delete(self, transaction_id: int) -> None:
        for i, transaction in enumerate(self._transactions):
            if transaction.id == transaction_id:
                logger.info(f"Удалена транзакция - {transaction} по id {transaction_id}")
                del self._transactions[i]
                return
        raise ValueError(f"Транзакция с id {transaction_id} не найдена")

    @log_action
    def save(self, repository: "TransactionRepository") -> None:
        repository.save(self._transactions)

    @log_action
    def load(self, repository: "TransactionRepository") -> None:
        self._transactions = repository.load()
        if self._transactions:
            max_id = max(t.id for t in self._transactions)
            Transaction._counter = max_id + 1
