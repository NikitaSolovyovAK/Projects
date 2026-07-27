from __future__ import annotations

from PySide6.QtCore import Signal #Для создания пользовательских сигналов
from PySide6.QtWidgets import (
    QComboBox,#выподающий список, горизонтальная запись, текстовая метка, кнопка, базовый класс
    QHBoxLayout,
    QLabel,
    QPushButton,
    QWidget,
)


class PaginationWidget(QWidget):# QWidget предоставляет фундаментальные возможности: отображение на экране, обработка событий, сигналы, стилизация, управление геометрией
    first_requested = Signal()
    previous_requested = Signal()
    next_requested = Signal()
    last_requested = Signal()
    page_size_changed = Signal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._build_ui()#Строит интерфейс

    def _build_ui(self) -> None:
        self.first_button = QPushButton('<<')
        self.previous_button = QPushButton('<')
        self.next_button = QPushButton('>')
        self.last_button = QPushButton('>>')

        self.page_size_label = QLabel('Записей на странице:')
        self.page_size_combo = QComboBox()
        self.page_size_combo.addItems(['5', '10', '20', '50'])
        self.page_size_combo.setCurrentText('10')

        self.page_info_label = QLabel('Страница 1 из 1')
        self.total_info_label = QLabel('Всего записей: 0')

        #Создание горизонтального расположения
        layout = QHBoxLayout()
        layout.addWidget(self.first_button)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.last_button)
        layout.addSpacing(16)
        layout.addWidget(self.page_size_label)
        layout.addWidget(self.page_size_combo)
        layout.addSpacing(16)
        layout.addWidget(self.page_info_label)
        layout.addStretch(1)
        layout.addWidget(self.total_info_label)
        self.setLayout(layout)

        #Подключение сигнала clicked каждой кнопки к соответствующему сигналу виджета, то есть при нажатии кнопки испускается нужный сигнал, который обрабатывается контроллером
        self.first_button.clicked.connect(self.first_requested.emit)
        self.previous_button.clicked.connect(self.previous_requested.emit)
        self.next_button.clicked.connect(self.next_requested.emit)
        self.last_button.clicked.connect(self.last_requested.emit)
        self.page_size_combo.currentTextChanged.connect(self._on_page_size_changed)

    def _on_page_size_changed(self, value: str) -> None:
        self.page_size_changed.emit(int(value))

    def current_page_size(self) -> int:
        return int(self.page_size_combo.currentText())

    #Обновляет текстовые метки информацией о текущей странице и общем количестве записей.
    def set_page_info(
        self,
        page_number: int,
        total_pages: int,
        total_items: int,
        items_on_page: int,
    ) -> None:
        self.page_info_label.setText(
            f'Страница {page_number} из {total_pages} | На странице: {items_on_page}'
        )
        self.total_info_label.setText(f'Всего записей: {total_items}')

        has_previous: bool = page_number > 1
        has_next: bool = page_number < total_pages
        self.first_button.setEnabled(has_previous)
        self.previous_button.setEnabled(has_previous)
        self.next_button.setEnabled(has_next)
        self.last_button.setEnabled(has_next)
