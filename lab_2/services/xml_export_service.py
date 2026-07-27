from __future__ import annotations

from pathlib import Path
from xml.dom import minidom

from train_schedule_app.models.train_record import TrainRecord


class XmlExportService:
    """Сохранение списка поездов в XML через DOM."""

    def export(self, file_path: str | Path, records: list[TrainRecord]) -> None:
        document: minidom.Document = minidom.Document()
        root = document.createElement('trains')
        document.appendChild(root)

        for record in records:
            train_element = document.createElement('train')
            if record.record_id is not None:
                train_element.setAttribute('id', str(record.record_id))

            fields = record.to_xml_dict()
            for field_name in (
                'train_number',
                'departure_station',
                'arrival_station',
                'departure_datetime',
                'arrival_datetime',
                'travel_minutes',
            ):
                field_element = document.createElement(field_name)
                field_element.appendChild(document.createTextNode(fields[field_name]))
                train_element.appendChild(field_element)

            root.appendChild(train_element)

        xml_text: str = document.toprettyxml(indent='    ', encoding='utf-8').decode('utf-8')
        Path(file_path).write_text(xml_text, encoding='utf-8')
