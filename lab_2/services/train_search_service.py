from __future__ import annotations

from train_schedule_app.models.search_criteria import (
    SearchCriteria,
    StationCriteria,
    TimeRangeCriteria,
    TrainNumberOrDateCriteria,
    TravelTimeCriteria,
)
from train_schedule_app.models.train_record import TrainRecord

#Сервис для поиска записей по различным критериям
class TrainSearchService:
    def search(
        self,
        records: list[TrainRecord],
        criteria: SearchCriteria,
    ) -> list[TrainRecord]:
        if isinstance(criteria, TrainNumberOrDateCriteria):
            return self._search_by_train_number_or_date(records, criteria)
        if isinstance(criteria, TimeRangeCriteria):
            return self._search_by_time_range(records, criteria)
        if isinstance(criteria, StationCriteria):
            return self._search_by_station(records, criteria)
        if isinstance(criteria, TravelTimeCriteria):
            return self._search_by_travel_time(records, criteria)
        return []

    def _search_by_train_number_or_date(
        self,
        records: list[TrainRecord],
        criteria: TrainNumberOrDateCriteria,
    ) -> list[TrainRecord]:
        result: list[TrainRecord] = []
        for record in records:
            by_number: bool = bool(criteria.train_number) and record.matches_train_number(
                criteria.train_number
            )
            by_date: bool = (
                criteria.departure_date is not None
                and record.matches_departure_date(criteria.departure_date)
            )
            if by_number or by_date:
                result.append(record)
        return result

    def _search_by_time_range(
        self,
        records: list[TrainRecord],
        criteria: TimeRangeCriteria,
    ) -> list[TrainRecord]:
        result: list[TrainRecord] = []
        for record in records:
            by_departure_time: bool = (
                criteria.departure_start is not None
                and criteria.departure_end is not None
                and record.departure_time_in_range(
                    criteria.departure_start,
                    criteria.departure_end,
                )
            )
            by_arrival_time: bool = (
                criteria.arrival_start is not None
                and criteria.arrival_end is not None
                and record.arrival_time_in_range(
                    criteria.arrival_start,
                    criteria.arrival_end,
                )
            )
            if by_departure_time or by_arrival_time:
                result.append(record)
        return result

    def _search_by_station(
        self,
        records: list[TrainRecord],
        criteria: StationCriteria,
    ) -> list[TrainRecord]:
        result: list[TrainRecord] = []
        for record in records:
            by_departure_station: bool = bool(
                criteria.departure_station
            ) and record.matches_departure_station(criteria.departure_station)
            by_arrival_station: bool = bool(
                criteria.arrival_station
            ) and record.matches_arrival_station(criteria.arrival_station)
            if by_departure_station or by_arrival_station:
                result.append(record)
        return result

    def _search_by_travel_time(
        self,
        records: list[TrainRecord],
        criteria: TravelTimeCriteria,
    ) -> list[TrainRecord]:
        if criteria.duration is None:
            return []
        return [record for record in records if record.matches_travel_time(criteria.duration)]
