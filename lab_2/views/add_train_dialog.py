from __future__ import annotations

from datetime import datetime

from PySide6.QtCore import QDateTime
from PySide6.QtWidgets import (
    QDateTimeEdit,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QVBoxLayout,
)

from train_schedule_app.models.train_record import TrainRecord, TrainValidationError


class AddTrainDialog(QDialog):
    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Добавление записи о поезде')
        self.resize(450, 260)
        self._build_ui()
        self._connect_signals()
        self._update_travel_time_label()

    def _build_ui(self) -> None:
        self.train_number_edit = QLineEdit()
        self.departure_station_edit = QLineEdit()
        self.arrival_station_edit = QLineEdit()

        current = QDateTime.currentDateTime()
        self.departure_datetime_edit = QDateTimeEdit(current)
        self.departure_datetime_edit.setCalendarPopup(True)
        self.departure_datetime_edit.setDisplayFormat('dd.MM.yyyy HH:mm')

        self.arrival_datetime_edit = QDateTimeEdit(current.addSecs(3600))
        self.arrival_datetime_edit.setCalendarPopup(True)
        self.arrival_datetime_edit.setDisplayFormat('dd.MM.yyyy HH:mm')

        self.travel_time_label = QLabel('0 ч 0 мин')

        form_layout = QFormLayout()
        form_layout.addRow('Номер поезда:', self.train_number_edit)
        form_layout.addRow('Станция отправления:', self.departure_station_edit)
        form_layout.addRow('Станция прибытия:', self.arrival_station_edit)
        form_layout.addRow('Дата и время отправления:', self.departure_datetime_edit)
        form_layout.addRow('Дата и время прибытия:', self.arrival_datetime_edit)
        form_layout.addRow('Время в пути:', self.travel_time_label)

        self.button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel
        )

        layout = QVBoxLayout()
        layout.addLayout(form_layout)
        layout.addWidget(self.button_box)
        self.setLayout(layout)

    #При изменении любой даты/времени вызывается _update_travel_time_label
    #Принятие кнопки OK вызывает _validate_and_accept, отмена – reject.
    def _connect_signals(self) -> None:
        self.departure_datetime_edit.dateTimeChanged.connect(
            self._update_travel_time_label
        )
        self.arrival_datetime_edit.dateTimeChanged.connect(
            self._update_travel_time_label
        )
        self.button_box.accepted.connect(self._validate_and_accept)
        self.button_box.rejected.connect(self.reject)

    def _update_travel_time_label(self) -> None:
        departure = self.departure_datetime_edit.dateTime().toPython()
        arrival = self.arrival_datetime_edit.dateTime().toPython()
        if arrival <= departure:
            self.travel_time_label.setText('Некорректный интервал')
            return
        delta = arrival - departure
        total_minutes = int(delta.total_seconds() // 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        self.travel_time_label.setText(f'{hours} ч {minutes} мин')

    def _validate_and_accept(self) -> None:
        try:
            self.get_record()
        except TrainValidationError as error:
            QMessageBox.warning(self, 'Ошибка валидации', str(error))
            return
        self.accept()

    def get_record(self) -> TrainRecord:
        departure_datetime: datetime = self.departure_datetime_edit.dateTime().toPython()
        arrival_datetime: datetime = self.arrival_datetime_edit.dateTime().toPython()
        return TrainRecord(
            train_number=self.train_number_edit.text(),
            departure_station=self.departure_station_edit.text(),
            arrival_station=self.arrival_station_edit.text(),
            departure_datetime=departure_datetime,
            arrival_datetime=arrival_datetime,
        )
