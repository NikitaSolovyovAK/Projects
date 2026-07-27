from __future__ import annotations

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Sequence

from train_schedule_app.models.train_record import TrainRecord
from train_schedule_app.repositories.train_repository import TrainRepository


class SQLiteTrainRepository(TrainRepository):
    def __init__(self, database_path: str | Path) -> None:# преобразует в Path, создает родительскую папку директорию если ее нет и вызывает метод для создания таблицы
        self.database_path: Path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize_database()

    def _get_connection(self) -> sqlite3.Connection:# возвращает соединение с базой данных
        connection: sqlite3.Connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize_database(self) -> None:
        with self._get_connection() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS trains (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    train_number TEXT NOT NULL,
                    departure_station TEXT NOT NULL,
                    arrival_station TEXT NOT NULL,
                    departure_datetime TEXT NOT NULL,
                    arrival_datetime TEXT NOT NULL,
                    travel_minutes INTEGER NOT NULL
                )
                """
            )

    def insert(self, record: TrainRecord) -> TrainRecord:
        with self._get_connection() as connection:
            cursor: sqlite3.Cursor = connection.execute(#Cursor - объект содержащий информацию о выполнении операции
                """
                INSERT INTO trains (
                    train_number,
                    departure_station,
                    arrival_station,
                    departure_datetime,
                    arrival_datetime,
                    travel_minutes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    record.train_number,
                    record.departure_station,
                    record.arrival_station,
                    record.departure_datetime.isoformat(),
                    record.arrival_datetime.isoformat(),
                    record.travel_minutes,
                ),
            )
            new_id: int = int(cursor.lastrowid)
        return record.with_record_id(new_id)

    def insert_many(self, records: list[TrainRecord]) -> None:
        if not records:
            return
        with self._get_connection() as connection:
            connection.executemany(
                """
                INSERT INTO trains (
                    train_number,
                    departure_station,
                    arrival_station,
                    departure_datetime,
                    arrival_datetime,
                    travel_minutes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        record.train_number,
                        record.departure_station,
                        record.arrival_station,
                        record.departure_datetime.isoformat(),
                        record.arrival_datetime.isoformat(),
                        record.travel_minutes,
                    )
                    for record in records
                ],
            )

    def get_all(self) -> list[TrainRecord]:
        with self._get_connection() as connection:
            rows = connection.execute(
                """
                SELECT
                    id,
                    train_number,
                    departure_station,
                    arrival_station,
                    departure_datetime,
                    arrival_datetime,
                    travel_minutes
                FROM trains
                ORDER BY departure_datetime, train_number
                """
            ).fetchall()

        records: list[TrainRecord] = []
        for row in rows:
            record = TrainRecord(
                train_number=str(row['train_number']),
                departure_station=str(row['departure_station']),
                arrival_station=str(row['arrival_station']),
                departure_datetime=datetime.fromisoformat(str(row['departure_datetime'])),
                arrival_datetime=datetime.fromisoformat(str(row['arrival_datetime'])),
                record_id=int(row['id']),
            )
            records.append(record)
        return records

    def replace_all(self, records: list[TrainRecord]) -> None:
        with self._get_connection() as connection:
            connection.execute('DELETE FROM trains')
            connection.executemany(#массово восстанавливает записи через executemany
                """
                INSERT INTO trains (
                    train_number,
                    departure_station,
                    arrival_station,
                    departure_datetime,
                    arrival_datetime,
                    travel_minutes
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        record.train_number,
                        record.departure_station,
                        record.arrival_station,
                        record.departure_datetime.isoformat(),
                        record.arrival_datetime.isoformat(),
                        record.travel_minutes,
                    )
                    for record in records
                ],
            )

    def delete_by_ids(self, record_ids: Sequence[int]) -> int:
        ids: list[int] = [int(record_id) for record_id in record_ids]
        if not ids:
            return 0
        placeholders: str = ','.join(['?'] * len(ids))
        with self._get_connection() as connection:
            cursor: sqlite3.Cursor = connection.execute(
                f'DELETE FROM trains WHERE id IN ({placeholders})',
                ids,
            )
            return int(cursor.rowcount)

    def clear(self) -> None:
        with self._get_connection() as connection:
            connection.execute('DELETE FROM trains')
