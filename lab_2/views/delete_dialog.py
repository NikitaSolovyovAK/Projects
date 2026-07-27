from __future__ import annotations

from datetime import date, time, timedelta

from PySide6.QtCore import QDate, QTime, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDateEdit,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QStackedWidget,
    QTimeEdit,
    QVBoxLayout,
    QWidget,
)

from train_schedule_app.models.search_criteria import (
    SearchCriteria,
    SearchMode,
    StationCriteria,
    TimeRangeCriteria,
    TrainNumberOrDateCriteria,
    TravelTimeCriteria,
)


class DeleteDialog(QDialog):
    delete_requested = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Удаление записей')
        self.resize(600, 420)
        self._build_ui()
        self._connect_signals()

    def _build_ui(self) -> None:
        self.mode_combo = QComboBox()
        self.mode_combo.addItem('По номеру поезда или дате отправления', SearchMode.TRAIN_NUMBER_OR_DATE)
        self.mode_combo.addItem('По диапазону времени отправления или прибытия', SearchMode.TIME_RANGE)
        self.mode_combo.addItem('По станции отправления или прибытия', SearchMode.STATION)
        self.mode_combo.addItem('По времени в пути', SearchMode.TRAVEL_TIME)

        self.criteria_stack = QStackedWidget()
        self.criteria_stack.addWidget(self._build_train_number_or_date_page())
        self.criteria_stack.addWidget(self._build_time_range_page())
        self.criteria_stack.addWidget(self._build_station_page())
        self.criteria_stack.addWidget(self._build_travel_time_page())

        self.delete_button = QPushButton('Удалить записи')
        self.close_button = QPushButton('Закрыть')

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.delete_button)
        buttons_layout.addWidget(self.close_button)
        buttons_layout.addStretch(1)

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Режим удаления:'))
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.criteria_stack)
        layout.addLayout(buttons_layout)
        self.setLayout(layout)

    def _connect_signals(self) -> None:
        self.mode_combo.currentIndexChanged.connect(self.criteria_stack.setCurrentIndex)
        self.delete_button.clicked.connect(self._emit_delete_requested)
        self.close_button.clicked.connect(self.close)

    def _build_train_number_or_date_page(self) -> QWidget:
        page = QWidget()
        self.delete_train_number_edit = QLineEdit()
        self.use_departure_date_checkbox = QCheckBox('Использовать дату отправления')
        self.delete_departure_date_edit = QDateEdit(QDate.currentDate())
        self.delete_departure_date_edit.setCalendarPopup(True)
        self.delete_departure_date_edit.setEnabled(False)
        self.use_departure_date_checkbox.toggled.connect(
            self.delete_departure_date_edit.setEnabled
        )

        form = QFormLayout()
        form.addRow('Номер поезда:', self.delete_train_number_edit)
        form.addRow(self.use_departure_date_checkbox, self.delete_departure_date_edit)
        page.setLayout(form)
        return page

    def _build_time_range_page(self) -> QWidget:
        page = QWidget()

        departure_group = QGroupBox('Диапазон времени отправления')
        self.use_departure_time_range_checkbox = QCheckBox('Использовать диапазон')
        self.delete_departure_time_start_edit = QTimeEdit(QTime(8, 0))
        self.delete_departure_time_end_edit = QTimeEdit(QTime(12, 0))
        self.delete_departure_time_start_edit.setDisplayFormat('HH:mm')
        self.delete_departure_time_end_edit.setDisplayFormat('HH:mm')
        self.delete_departure_time_start_edit.setEnabled(False)
        self.delete_departure_time_end_edit.setEnabled(False)
        self.use_departure_time_range_checkbox.toggled.connect(
            self.delete_departure_time_start_edit.setEnabled
        )
        self.use_departure_time_range_checkbox.toggled.connect(
            self.delete_departure_time_end_edit.setEnabled
        )
        departure_form = QFormLayout()
        departure_form.addRow(self.use_departure_time_range_checkbox)
        departure_form.addRow('От:', self.delete_departure_time_start_edit)
        departure_form.addRow('До:', self.delete_departure_time_end_edit)
        departure_group.setLayout(departure_form)

        arrival_group = QGroupBox('Диапазон времени прибытия')
        self.use_arrival_time_range_checkbox = QCheckBox('Использовать диапазон')
        self.delete_arrival_time_start_edit = QTimeEdit(QTime(13, 0))
        self.delete_arrival_time_end_edit = QTimeEdit(QTime(18, 0))
        self.delete_arrival_time_start_edit.setDisplayFormat('HH:mm')
        self.delete_arrival_time_end_edit.setDisplayFormat('HH:mm')
        self.delete_arrival_time_start_edit.setEnabled(False)
        self.delete_arrival_time_end_edit.setEnabled(False)
        self.use_arrival_time_range_checkbox.toggled.connect(
            self.delete_arrival_time_start_edit.setEnabled
        )
        self.use_arrival_time_range_checkbox.toggled.connect(
            self.delete_arrival_time_end_edit.setEnabled
        )
        arrival_form = QFormLayout()
        arrival_form.addRow(self.use_arrival_time_range_checkbox)
        arrival_form.addRow('От:', self.delete_arrival_time_start_edit)
        arrival_form.addRow('До:', self.delete_arrival_time_end_edit)
        arrival_group.setLayout(arrival_form)

        layout = QHBoxLayout()
        layout.addWidget(departure_group)
        layout.addWidget(arrival_group)
        page.setLayout(layout)
        return page

    def _build_station_page(self) -> QWidget:
        page = QWidget()
        self.delete_departure_station_edit = QLineEdit()
        self.delete_arrival_station_edit = QLineEdit()

        form = QFormLayout()
        form.addRow('Станция отправления:', self.delete_departure_station_edit)
        form.addRow('Станция прибытия:', self.delete_arrival_station_edit)
        page.setLayout(form)
        return page

    def _build_travel_time_page(self) -> QWidget:
        page = QWidget()
        self.delete_travel_hours_spin = QSpinBox()
        self.delete_travel_hours_spin.setRange(0, 200)
        self.delete_travel_minutes_spin = QSpinBox()
        self.delete_travel_minutes_spin.setRange(0, 59)

        form = QFormLayout()
        form.addRow('Часы:', self.delete_travel_hours_spin)
        form.addRow('Минуты:', self.delete_travel_minutes_spin)
        page.setLayout(form)
        return page

    def _emit_delete_requested(self) -> None:
        criteria = self.build_criteria()
        if criteria is None:
            return
        self.delete_requested.emit(criteria)

    def build_criteria(self) -> SearchCriteria | None:
        mode: SearchMode = self.current_mode()

        if mode == SearchMode.TRAIN_NUMBER_OR_DATE:
            departure_date: date | None = None
            if self.use_departure_date_checkbox.isChecked():
                departure_date = self.delete_departure_date_edit.date().toPython()
            criteria = TrainNumberOrDateCriteria(
                train_number=self.delete_train_number_edit.text(),
                departure_date=departure_date,
            )
            if not criteria.is_valid():
                self._show_validation_message('Введите номер поезда и/или выберите дату отправления.')
                return None
            return criteria

        if mode == SearchMode.TIME_RANGE:
            departure_start: time | None = None
            departure_end: time | None = None
            arrival_start: time | None = None
            arrival_end: time | None = None
            if self.use_departure_time_range_checkbox.isChecked():
                departure_start = self.delete_departure_time_start_edit.time().toPython()
                departure_end = self.delete_departure_time_end_edit.time().toPython()
            if self.use_arrival_time_range_checkbox.isChecked():
                arrival_start = self.delete_arrival_time_start_edit.time().toPython()
                arrival_end = self.delete_arrival_time_end_edit.time().toPython()
            criteria = TimeRangeCriteria(
                departure_start=departure_start,
                departure_end=departure_end,
                arrival_start=arrival_start,
                arrival_end=arrival_end,
            )
            if not criteria.is_valid():
                self._show_validation_message('Включите хотя бы один диапазон времени.')
                return None
            return criteria

        if mode == SearchMode.STATION:
            criteria = StationCriteria(
                departure_station=self.delete_departure_station_edit.text(),
                arrival_station=self.delete_arrival_station_edit.text(),
            )
            if not criteria.is_valid():
                self._show_validation_message('Введите станцию отправления и/или станцию прибытия.')
                return None
            return criteria

        duration = timedelta(
            hours=self.delete_travel_hours_spin.value(),
            minutes=self.delete_travel_minutes_spin.value(),
        )
        return TravelTimeCriteria(duration=duration)

    def current_mode(self) -> SearchMode:
        return SearchMode(self.mode_combo.currentData())

    def _show_validation_message(self, message: str) -> None:
        QMessageBox.warning(self, 'Некорректные условия удаления', message)
