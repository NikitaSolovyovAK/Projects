from __future__ import annotations #позволяет использовать аннотации типов с отложенным вычислением

from datetime import date, datetime, time, timedelta
from typing import Any


class TrainValidationError(ValueError):
    """Ошибка валидации данных записи о поезде."""


class TrainRecord:
    """Модель одной записи о поезде."""

    def __init__(
        self,
        train_number: str,
        departure_station: str,
        arrival_station: str,
        departure_datetime: datetime,
        arrival_datetime: datetime,
        record_id: int | None = None, #идентификатор на случай если запись уже есть в БД
    ) -> None:
        self.record_id: int | None = record_id
        self.train_number: str = train_number.strip()
        self.departure_station: str = departure_station.strip()
        self.arrival_station: str = arrival_station.strip()
        self.departure_datetime: datetime = departure_datetime
        self.arrival_datetime: datetime = arrival_datetime

        self._validate_required_fields()
        self._validate_route()
        self._validate_datetimes()

        self.travel_time: timedelta = self.arrival_datetime - self.departure_datetime

    def _validate_required_fields(self) -> None:
        if not self.train_number:
            raise TrainValidationError('Номер поезда не может быть пустым.')
        if not self.departure_station:
            raise TrainValidationError('Станция отправления не может быть пустой.')
        if not self.arrival_station:
            raise TrainValidationError('Станция прибытия не может быть пустой.')

    def _validate_route(self) -> None:
        if self.departure_station.lower() == self.arrival_station.lower():
            raise TrainValidationError(
                'Станции отправления и прибытия не должны совпадать.'
            )

    def _validate_datetimes(self) -> None:
        if self.arrival_datetime <= self.departure_datetime:
            raise TrainValidationError(
                'Дата и время прибытия должны быть позже даты и времени отправления.'
            )

    @property
    def departure_date(self) -> date:
        return self.departure_datetime.date()

    @property
    def departure_time(self) -> time:
        return self.departure_datetime.time()

    @property
    def arrival_date(self) -> date:
        return self.arrival_datetime.date()

    @property
    def arrival_time(self) -> time:
        return self.arrival_datetime.time()

    @property
    def travel_minutes(self) -> int:
        return int(self.travel_time.total_seconds() // 60)

    def get_travel_time_display(self) -> str:
        hours: int = self.travel_minutes // 60
        minutes: int = self.travel_minutes % 60
        return f'{hours} ч {minutes} мин'

    #проверка на совпадение с заданным критерием
    def matches_train_number(self, value: str) -> bool:
        return self.train_number.lower() == value.strip().lower()

    def matches_departure_date(self, value: date) -> bool:
        return self.departure_date == value

    def matches_departure_station(self, value: str) -> bool:
        return self.departure_station.lower() == value.strip().lower()

    def matches_arrival_station(self, value: str) -> bool:
        return self.arrival_station.lower() == value.strip().lower()

    def matches_travel_time(self, value: timedelta) -> bool:
        return self.travel_time == value

    #проверка: попадает ли время в заданный интервал
    def departure_time_in_range(self, start: time, end: time) -> bool:
        return self._time_in_range(self.departure_time, start, end)

    def arrival_time_in_range(self, start: time, end: time) -> bool:
        return self._time_in_range(self.arrival_time, start, end)

    @staticmethod
    def _time_in_range(value: time, start: time, end: time) -> bool:
        if start <= end:
            return start <= value <= end
        return value >= start or value <= end

    def with_record_id(self, record_id: int) -> 'TrainRecord':
        return TrainRecord(
            train_number=self.train_number,
            departure_station=self.departure_station,
            arrival_station=self.arrival_station,
            departure_datetime=self.departure_datetime,
            arrival_datetime=self.arrival_datetime,
            record_id=record_id,
        )

    def to_xml_dict(self) -> dict[str, str]:
        return {
            'id': '' if self.record_id is None else str(self.record_id),
            'train_number': self.train_number,
            'departure_station': self.departure_station,
            'arrival_station': self.arrival_station,
            'departure_datetime': self.departure_datetime.isoformat(),
            'arrival_datetime': self.arrival_datetime.isoformat(),
            'travel_minutes': str(self.travel_minutes),
        }

    def to_table_row(self) -> list[str]:
        return [
            self.train_number,
            self.departure_station,
            self.arrival_station,
            self.departure_datetime.strftime('%d.%m.%Y %H:%M'),
            self.arrival_datetime.strftime('%d.%m.%Y %H:%M'),
            self.get_travel_time_display(),
        ]

    #строковое представление для отладки
    def __repr__(self) -> str:
        return (
            'TrainRecord('
            f'record_id={self.record_id}, '
            f'train_number={self.train_number!r}, '
            f'departure_station={self.departure_station!r}, '
            f'arrival_station={self.arrival_station!r}, '
            f'departure_datetime={self.departure_datetime!r}, '
            f'arrival_datetime={self.arrival_datetime!r}'
            ')'
        )

    def __eq__(self, other: Any) -> bool:
        if not isinstance(other, TrainRecord):
            return False
        return (
            self.record_id == other.record_id
            and self.train_number == other.train_number
            and self.departure_station == other.departure_station
            and self.arrival_station == other.arrival_station
            and self.departure_datetime == other.departure_datetime
            and self.arrival_datetime == other.arrival_datetime
        )
