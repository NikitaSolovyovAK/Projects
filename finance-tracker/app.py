from datetime import date as date_type

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, ConfigDict, Field

from models import Transaction, TransactionManager, TransactionType
from repository import JsonRepository
from stats import TransactionStats

repository = JsonRepository("data.json")
manager = TransactionManager()
manager.load(repository)

app = FastAPI(title="Finance Tracker")


class TransactionIn(BaseModel):
    amount: int = Field(gt=0)
    transaction_type: TransactionType
    description: str = ""
    category: str = ""
    date: date_type | None = None


class TransactionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    amount: int
    date: date_type
    description: str
    category: str
    transaction_type: TransactionType


class StatsOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
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
    category_expenses: dict[str, float]


@app.get("/api/transactions", response_model=list[TransactionOut])
def list_transactions():
    return manager.get_all()


@app.post("/api/transactions", response_model=TransactionOut, status_code=201)
def create_transaction(data: TransactionIn):
    try:
        transaction = Transaction(
            amount=data.amount,
            transaction_type=data.transaction_type,
            transaction_date=data.date,
            description=data.description,
            category=data.category,
        )
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error))
    manager.add_transaction(transaction)
    manager.save(repository)
    return transaction


@app.get("/api/transactions/{transaction_id}", response_model=TransactionOut)
def get_transaction(transaction_id: int):
    transaction = manager.get_by_id(transaction_id)
    if transaction is None:
        raise HTTPException(status_code=404, detail="Транзакция не найдена")
    return transaction


@app.delete("/api/transactions/{transaction_id}", status_code=204)
def delete_transaction(transaction_id: int):
    try:
        manager.delete(transaction_id)
    except ValueError as error:
        raise HTTPException(status_code=404, detail=str(error))
    manager.save(repository)


@app.get("/api/stats", response_model=StatsOut)
def get_stats():
    return TransactionStats().calculate(manager.get_all())


@app.get("/")
def index():
    return FileResponse("static/index.html")
