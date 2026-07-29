import os
from decimal import Decimal

import psycopg2

from decorators import timed
from logger import logger
from models import Transaction
from repository import TransactionRepository


class PostgresRepository(TransactionRepository):
    def __init__(self, host=None, port=None, database=None, user=None, password=None) -> None:
        self.host = host or os.environ.get("DB_HOST", "localhost")
        self.port = port or int(os.environ.get("DB_PORT", "5432"))
        self.database = database or os.environ.get("DB_NAME", "finance_tracker")
        self.user = user or os.environ.get("DB_USER", "postgres")
        self.password = password if password is not None else os.environ.get("DB_PASSWORD", "")
        self._ensure_table()

    def _connect(self):
        return psycopg2.connect(host=self.host, port=self.port, database=self.database, user=self.user, password=self.password)

    def _ensure_table(self) -> None:
        with self._connect() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    CREATE TABLE IF NOT EXISTS transactions (
                        id INTEGER PRIMARY KEY,
                        amount NUMERIC(12, 2) NOT NULL,
                        date DATE NOT NULL,
                        description TEXT DEFAULT '',
                        category TEXT DEFAULT '',
                        transaction_type TEXT NOT NULL
                    )
                    """
                )

    @staticmethod
    def _to_number(value):
        if isinstance(value, Decimal):
            return int(value) if value == value.to_integral_value() else float(value)
        return value

    @timed
    def save(self, transactions: list[Transaction]) -> None:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM transactions")
                    cur.executemany(
                        """
                        INSERT INTO transactions
                            (id, amount, date, description, category, transaction_type)
                        VALUES (%s, %s, %s, %s, %s, %s)
                        """,
                        [(t.id, t.amount, t.date, t.description, t.category, t.transaction_type.value) for t in transactions],
                    )
            logger.info(f"Сохранено {len(transactions)} транзакций в PostgreSQL")
        except Exception as e:
            logger.error(f"Ошибка при сохранении в PostgreSQL: {e}")
            raise

    @timed
    def load(self) -> list[Transaction]:
        try:
            with self._connect() as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT id, amount, date, description, category, transaction_type
                        FROM transactions
                        ORDER BY id
                        """
                    )
                    rows = cur.fetchall()
            transactions = []
            for row in rows:
                item = {
                    "id": row[0],
                    "amount": self._to_number(row[1]),
                    "date": row[2].isoformat(),
                    "description": row[3] or "",
                    "category": row[4] or "",
                    "transaction_type": row[5],
                }
                transactions.append(Transaction.from_dict(item))
            logger.info(f"Загружено {len(transactions)} транзакций из PostgreSQL")
            return transactions
        except Exception as e:
            logger.error(f"Ошибка загрузки из PostgreSQL: {e}")
            raise
