from models import TransactionManager, Transaction
from logger import logger


class TransactionBatch:
    def __init__(self, manager: TransactionManager):
        self._manager = manager

    def __enter__(self):
        self._pending = []
        return self

    def add(self, transaction: Transaction):
        self._pending.append(transaction)

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            for t in self._pending:
                self._manager.add_transaction(t)
        else:
            logger.info(f"Откат из-за ошибки: {exc_val}")
