from __future__ import annotations

from datetime import date, time, timedelta

from PySide6.QtCore import QDate, QTime, Signal, Qt
from PySide6.QtWidgets import (
    QAbstractItemView,
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
    QTableWidget,
    QTableWidgetItem,
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
from train_schedule_app.models.train_record import TrainRecord
from train_schedule_app.views.pagination_widget import PaginationWidget


class SearchDialog(QDialog):
    search_requested = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle('Поиск записей')
        self.resize(1100, 700)
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

        self.search_button = QPushButton('Найти')
        self.close_button = QPushButton('Закрыть')

        buttons_layout = QHBoxLayout()
        buttons_layout.addWidget(self.search_button)
        buttons_layout.addWidget(self.close_button)
        buttons_layout.addStretch(1)

        self.result_summary_label = QLabel('Найдено записей: 0')
        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels(
            [
                'Номер поезда',
                'Станция отправления',
                'Станция прибытия',
                'Дата и время отправления',
                'Дата и время прибытия',
                'Время в пути',
            ]
        )
        self.results_table.horizontalHeader().setStretchLastSection(True)
        self.results_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.results_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.results_table.setAlternatingRowColors(True)

        self.pagination_widget = PaginationWidget()

        layout = QVBoxLayout()
        layout.addWidget(QLabel('Режим поиска:'))
        layout.addWidget(self.mode_combo)
        layout.addWidget(self.criteria_stack)
        layout.addLayout(buttons_layout)
        layout.addWidget(self.result_summary_label)
        layout.addWidget(self.results_table)
        layout.addWidget(self.pagination_widget)
        self.setLayout(layout)

    def _connect_signals(self) -> None:
        self.mode_combo.currentIndexChanged.connect(self.criteria_stack.setCurrentIndex)#при смене режима автоматически переключается страница с соответствующими полями ввода
        self.search_button.clicked.connect(self._emit_search_requested)
        self.close_button.clicked.connect(self.close)

    def _build_train_number_or_date_page(self) -> QWidget:
        page = QWidget()
        self.search_train_number_edit = QLineEdit()
        self.use_departure_date_checkbox = QCheckBox('Использовать дату отправления')
        self.search_departure_date_edit = QDateEdit(QDate.currentDate())
        self.search_departure_date_edit.setCalendarPopup(True)
        self.search_departure_date_edit.setEnabled(False)
        self.use_departure_date_checkbox.toggled.connect(
            self.search_departure_date_edit.setEnabled
        )

        form = QFormLayout()
        form.addRow('Номер поезда:', self.search_train_number_edit)
        form.addRow(self.use_departure_date_checkbox, self.search_departure_date_edit)
        page.setLayout(form)
        return page

    def _build_time_range_page(self) -> QWidget:
        page = QWidget()

        departure_group = QGroupBox('Диапазон времени отправления')
        self.use_departure_time_range_checkbox = QCheckBox('Использовать диапазон')
        self.departure_time_start_edit = QTimeEdit(QTime(8, 0))
        self.departure_time_end_edit = QTimeEdit(QTime(12, 0))
        self.departure_time_start_edit.setDisplayFormat('HH:mm')
        self.departure_time_end_edit.setDisplayFormat('HH:mm')
        self.departure_time_start_edit.setEnabled(False)
        self.departure_time_end_edit.setEnabled(False)
        self.use_departure_time_range_checkbox.toggled.connect(
            self.departure_time_start_edit.setEnabled
        )
        self.use_departure_time_range_checkbox.toggled.connect(
            self.departure_time_end_edit.setEnabled
        )
        departure_form = QFormLayout()
        departure_form.addRow(self.use_departure_time_range_checkbox)
        departure_form.addRow('От:', self.departure_time_start_edit)
        departure_form.addRow('До:', self.departure_time_end_edit)
        departure_group.setLayout(departure_form)

        arrival_group = QGroupBox('Диапазон времени прибытия')
        self.use_arrival_time_range_checkbox = QCheckBox('Использовать диапазон')
        self.arrival_time_start_edit = QTimeEdit(QTime(13, 0))
        self.arrival_time_end_edit = QTimeEdit(QTime(18, 0))
        self.arrival_time_start_edit.setDisplayFormat('HH:mm')
        self.arrival_time_end_edit.setDisplayFormat('HH:mm')
        self.arrival_time_start_edit.setEnabled(False)
        self.arrival_time_end_edit.setEnabled(False)
        self.use_arrival_time_range_checkbox.toggled.connect(
            self.arrival_time_start_edit.setEnabled
        )
        self.use_arrival_time_range_checkbox.toggled.connect(
            self.arrival_time_end_edit.setEnabled
        )
        arrival_form = QFormLayout()
        arrival_form.addRow(self.use_arrival_time_range_checkbox)
        arrival_form.addRow('От:', self.arrival_time_start_edit)
        arrival_form.addRow('До:', self.arrival_time_end_edit)
        arrival_group.setLayout(arrival_form)

        layout = QHBoxLayout()
        layout.addWidget(departure_group)
        layout.addWidget(arrival_group)
        page.setLayout(layout)
        return page

    def _build_station_page(self) -> QWidget:
        page = QWidget()
        self.search_departure_station_edit = QLineEdit()
        self.search_arrival_station_edit = QLineEdit()

        form = QFormLayout()
        form.addRow('Станция отправления:', self.search_departure_station_edit)
        form.addRow('Станция прибытия:', self.search_arrival_station_edit)
        page.setLayout(form)
        return page

    def _build_travel_time_page(self) -> QWidget:
        page = QWidget()
        self.travel_hours_spin = QSpinBox()
        self.travel_hours_spin.setRange(0, 200)
        self.travel_minutes_spin = QSpinBox()
        self.travel_minutes_spin.setRange(0, 59)

        form = QFormLayout()
        form.addRow('Часы:', self.travel_hours_spin)
        form.addRow('Минуты:', self.travel_minutes_spin)
        page.setLayout(form)
        return page

    #Вызывается при нажатии кнопки Найти
    def _emit_search_requested(self) -> None:
        criteria = self.build_criteria()
        if criteria is None:
            return
        self.search_requested.emit(criteria)
    #Этот метод создаёт объект критерия в зависимости от текущего режима
    def build_criteria(self) -> SearchCriteria | None:
        mode: SearchMode = self.current_mode()

        if mode == SearchMode.TRAIN_NUMBER_OR_DATE:
            departure_date: date | None = None
            if self.use_departure_date_checkbox.isChecked():
                departure_date = self.search_departure_date_edit.date().toPython()
            criteria = TrainNumberOrDateCriteria(
                train_number=self.search_train_number_edit.text(),
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
                departure_start = self.departure_time_start_edit.time().toPython()
                departure_end = self.departure_time_end_edit.time().toPython()
            if self.use_arrival_time_range_checkbox.isChecked():
                arrival_start = self.arrival_time_start_edit.time().toPython()
                arrival_end = self.arrival_time_end_edit.time().toPython()
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
                departure_station=self.search_departure_station_edit.text(),
                arrival_station=self.search_arrival_station_edit.text(),
            )
            if not criteria.is_valid():
                self._show_validation_message('Введите станцию отправления и/или станцию прибытия.')
                return None
            return criteria

        duration = timedelta(
            hours=self.travel_hours_spin.value(),
            minutes=self.travel_minutes_spin.value(),
        )
        return TravelTimeCriteria(duration=duration)

    def current_mode(self) -> SearchMode:
        return SearchMode(self.mode_combo.currentData())

    def show_results(
        self,
        records: list[TrainRecord],
        page_number: int,
        total_pages: int,
        total_items: int,
    ) -> None:
        self.result_summary_label.setText(f'Найдено записей: {total_items}')
        self.results_table.setRowCount(len(records))
        for row_index, record in enumerate(records):
            for column_index, value in enumerate(record.to_table_row()):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.results_table.setItem(row_index, column_index, item)
        self.results_table.resizeColumnsToContents()
        self.pagination_widget.set_page_info(
            page_number=page_number,
            total_pages=total_pages,
            total_items=total_items,
            items_on_page=len(records),
        )

    def current_page_size(self) -> int:
        return self.pagination_widget.current_page_size()

    def _show_validation_message(self, message: str) -> None:
        QMessageBox.warning(self, 'Некорректные условия поиска', message)
