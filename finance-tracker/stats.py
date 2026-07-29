from collections import defaultdict
from dataclasses import dataclass
from typing import Dict

from models import Transaction, TransactionType


@dataclass
class StatsResult:
    total_income: float
    total_expense: float
    balance: float
    total_count: int
    count_income: int
    count_expense: int
    max_income: float
    max_expense: float
    average_income: float
    average_expense: float
    category_expenses: Dict[str, float]


class TransactionStats:

    def calculate(self, transactions: list[Transaction]) -> StatsResult:
        total_income = 0.0
        total_expense = 0.0
        count_income = 0
        count_expense = 0
        max_income = 0.0
        max_expense = 0.0
        category_expenses = defaultdict(float)

        for t in transactions:
            if t.transaction_type == TransactionType.INCOME:
                total_income += t.amount
                count_income += 1
                if t.amount > max_income:
                    max_income = t.amount
            else:
                total_expense += t.amount
                count_expense += 1
                if t.amount > max_expense:
                    max_expense = t.amount
                category_expenses[t.category] += t.amount

        balance = total_income - total_expense
        total_count = len(transactions)

        average_income = total_income / count_income if count_income > 0 else 0.0
        average_expense = total_expense / count_expense if count_expense > 0 else 0.0

        category_expenses_dict = dict(category_expenses)

        return StatsResult(
            total_income=total_income,
            total_expense=total_expense,
            balance=balance,
            total_count=total_count,
            count_income=count_income,
            count_expense=count_expense,
            max_income=max_income,
            max_expense=max_expense,
            average_income=average_income,
            average_expense=average_expense,
            category_expenses=category_expenses_dict,
        )
