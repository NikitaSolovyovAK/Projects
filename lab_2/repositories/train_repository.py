from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Sequence

from train_schedule_app.models.train_record import TrainRecord


class TrainRepository(ABC):
    """Абстракция хранилища записей о поездах."""

    @abstractmethod
    def insert(self, record: TrainRecord) -> TrainRecord:
        raise NotImplementedError

    @abstractmethod
    def insert_many(self, records: list[TrainRecord]) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_all(self) -> list[TrainRecord]:
        raise NotImplementedError

    @abstractmethod
    def replace_all(self, records: list[TrainRecord]) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_by_ids(self, record_ids: Sequence[int]) -> int:
        raise NotImplementedError

    @abstractmethod
    def clear(self) -> None:
        raise NotImplementedError

