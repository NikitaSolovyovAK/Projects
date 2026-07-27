from __future__ import annotations

from datetime import datetime
from pathlib import Path
from xml.sax import ContentHandler, parse

from train_schedule_app.models.train_record import TrainRecord


class _TrainContentHandler(ContentHandler):
    def __init__(self) -> None:
        super().__init__()
        self.records: list[TrainRecord] = []
        self.current_train: dict[str, str] | None = None
        self.current_element_name: str = ''
        self.buffer: list[str] = []

    def startElement(self, name: str, attrs) -> None:
        self.current_element_name = name
        self.buffer = []
        if name == 'train':
            self.current_train = {}
            train_id: str = attrs.get('id', '')
            if train_id:
                self.current_train['id'] = train_id

    def characters(self, content: str) -> None:#для текстового содержимого между тегами
        if self.current_element_name:
            self.buffer.append(content)

    def endElement(self, name: str) -> None:
        text_value: str = ''.join(self.buffer).strip()
        if self.current_train is not None and name in {
            'train_number',
            'departure_station',
            'arrival_station',
            'departure_datetime',
            'arrival_datetime',
            'travel_minutes',
        }:
            self.current_train[name] = text_value

        if name == 'train' and self.current_train is not None:
            record_id: int | None = None
            if self.current_train.get('id'):
                record_id = int(self.current_train['id'])
            record = TrainRecord(
                train_number=self.current_train['train_number'],
                departure_station=self.current_train['departure_station'],
                arrival_station=self.current_train['arrival_station'],
                departure_datetime=datetime.fromisoformat(
                    self.current_train['departure_datetime']
                ),
                arrival_datetime=datetime.fromisoformat(
                    self.current_train['arrival_datetime']
                ),
                record_id=record_id,
            )
            self.records.append(record)
            self.current_train = None

        self.current_element_name = ''
        self.buffer = []


class XmlImportService:
    """Загрузка списка поездов из XML через SAX."""

    def import_records(self, file_path: str | Path) -> list[TrainRecord]:
        handler = _TrainContentHandler()
        parse(str(Path(file_path)), handler)
        return handler.records
