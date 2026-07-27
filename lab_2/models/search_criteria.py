from __future__ import annotations

from datetime import date, time, timedelta
from enum import Enum

#представление критериев поиска/удаления а также перечисление режимов
class SearchMode(str, Enum):
    TRAIN_NUMBER_OR_DATE = 'train_number_or_date'
    TIME_RANGE = 'time_range'
    STATION = 'station'
    TRAVEL_TIME = 'travel_time'


class TrainNumberOrDateCriteria:
    def __init__(
        self,
        train_number: str = '',
        departure_date: date | None = None,
    ) -> None:
        self.train_number: str = train_number.strip()
        self.departure_date: date | None = departure_date

    def is_valid(self) -> bool:
        return bool(self.train_number) or self.departure_date is not None


class TimeRangeCriteria:
    def __init__(
        self,
        departure_start: time | None = None,
        departure_end: time | None = None,
        arrival_start: time | None = None,
        arrival_end: time | None = None,
    ) -> None:
        self.departure_start: time | None = departure_start
        self.departure_end: time | None = departure_end
        self.arrival_start: time | None = arrival_start
        self.arrival_end: time | None = arrival_end

    def is_valid(self) -> bool:
        has_departure_range: bool = (
            self.departure_start is not None and self.departure_end is not None
        )
        has_arrival_range: bool = (
            self.arrival_start is not None and self.arrival_end is not None
        )
        return has_departure_range or has_arrival_range


class StationCriteria:
    def __init__(
        self,
        departure_station: str = '',
        arrival_station: str = '',
    ) -> None:
        self.departure_station: str = departure_station.strip()
        self.arrival_station: str = arrival_station.strip()

    def is_valid(self) -> bool:
        return bool(self.departure_station) or bool(self.arrival_station)


class TravelTimeCriteria:
    def __init__(self, duration: timedelta | None = None) -> None:
        self.duration: timedelta | None = duration

    def is_valid(self) -> bool:
        return self.duration is not None


SearchCriteria = (
    TrainNumberOrDateCriteria | TimeRangeCriteria | StationCriteria | TravelTimeCriteria
)
