from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QAction#Для создания действий меню
from PySide6.QtWidgets import (
    QAbstractItemView,
    QMainWindow,# Базовый класс главного окна, для отображения информационных сообщений и ошибок сообщений, строка состояний, таблица и её элементы, виджет с вкладками, панель инструментов, дерево и его элементы, для компоновки центрального виджета
    QMessageBox,
    QStatusBar,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QToolBar,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from train_schedule_app.models.train_record import TrainRecord
from train_schedule_app.views.pagination_widget import PaginationWidget


class MainWindow(QMainWindow):
    add_requested = Signal()
    search_requested = Signal()
    delete_requested = Signal()
    save_xml_requested = Signal()
    load_xml_requested = Signal()
    open_database_requested = Signal()
    save_database_as_requested = Signal()

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle('Лабораторная работа №2 — Поезда (вариант 13)')
        self.resize(1200, 750)

        self._build_actions()
        self._build_menu()
        self._build_toolbar()
        self._build_central_widget()
        self.setStatusBar(QStatusBar())

    def _build_actions(self) -> None:
        self.add_action = QAction('Добавить запись', self) #Создает объекст с текстом и родителем
        #Подключает trigger каждого действия к соответствуещему сигналу главного окна.
        self.add_action.triggered.connect(self.add_requested.emit)

        self.search_action = QAction('Поиск', self)
        self.search_action.triggered.connect(self.search_requested.emit)

        self.delete_action = QAction('Удаление', self)
        self.delete_action.triggered.connect(self.delete_requested.emit)

        self.save_xml_action = QAction('Сохранить XML', self)
        self.save_xml_action.triggered.connect(self.save_xml_requested.emit)

        self.load_xml_action = QAction('Загрузить XML', self)
        self.load_xml_action.triggered.connect(self.load_xml_requested.emit)

        self.open_database_action = QAction('Открыть БД', self)
        self.open_database_action.triggered.connect(self.open_database_requested.emit)

        self.save_database_as_action = QAction('Сохранить БД как', self)
        self.save_database_as_action.triggered.connect(
            self.save_database_as_requested.emit
        )

        self.exit_action = QAction('Выход', self)
        self.exit_action.triggered.connect(self.close)

    def _build_menu(self) -> None:
        menu_bar = self.menuBar()
        menu_bar.clear()

        file_menu = menu_bar.addMenu('Файл')
        file_menu.addAction(self.save_xml_action)
        file_menu.addAction(self.load_xml_action)
        file_menu.addSeparator()
        file_menu.addAction(self.open_database_action)
        file_menu.addAction(self.save_database_as_action)
        file_menu.addSeparator()
        file_menu.addAction(self.exit_action)

        records_menu = menu_bar.addMenu('Записи')
        records_menu.addAction(self.add_action)
        records_menu.addAction(self.search_action)
        records_menu.addAction(self.delete_action)

    def _build_toolbar(self) -> None:
        toolbar = QToolBar('Основные команды')
        self.addToolBar(toolbar)
        toolbar.addAction(self.add_action)
        toolbar.addAction(self.search_action)
        toolbar.addAction(self.delete_action)
        toolbar.addSeparator()
        toolbar.addAction(self.save_xml_action)
        toolbar.addAction(self.load_xml_action)
        toolbar.addSeparator()
        toolbar.addAction(self.open_database_action)
        toolbar.addAction(self.save_database_as_action)

    def _build_central_widget(self) -> None:
        #Создание центрального виджета и вертикального layout
        central_widget = QWidget()
        layout = QVBoxLayout()

        self.tab_widget = QTabWidget()#Создание виджета с вкладками(Таблица и Дерево)
        self.table_widget = QTableWidget(0, 6)
        self.table_widget.setHorizontalHeaderLabels(
            [
                'Номер поезда',
                'Станция отправления',
                'Станция прибытия',
                'Дата и время отправления',
                'Дата и время прибытия',
                'Время в пути',
            ]
        )
        self.table_widget.horizontalHeader().setStretchLastSection(True)#horizontalHeader() возвращает объект заголовка таблицы.
            #setStretchLastSection(True) — последняя колонка (время в пути) будет автоматически растягиваться, чтобы заполнить всё доступное пространство таблицы
        self.table_widget.setEditTriggers(QAbstractItemView.NoEditTriggers)#Запрещает редактировать ячейки, по умолчанию можно нажав 2 раза
        self.table_widget.setSelectionBehavior(QAbstractItemView.SelectRows)#Выделение целыми строками
        self.table_widget.setAlternatingRowColors(True)#чередование цвета строк

        self.tree_widget = QTreeWidget()#Виджет дерева с 2 столбцами
        self.tree_widget.setHeaderLabels(['Поле', 'Значение'])

        self.tab_widget.addTab(self.table_widget, 'Таблица')
        self.tab_widget.addTab(self.tree_widget, 'Дерево')

        self.pagination_widget = PaginationWidget()

        layout.addWidget(self.tab_widget)
        layout.addWidget(self.pagination_widget)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def show_records(
        self,
        records: list[TrainRecord],
        page_number: int,
        total_pages: int,
        total_items: int,
    ) -> None:
        self._fill_table(records)
        self._fill_tree(records)
        self.pagination_widget.set_page_info(
            page_number=page_number,
            total_pages=total_pages,
            total_items=total_items,
            items_on_page=len(records),
        )

    def _fill_table(self, records: list[TrainRecord]) -> None:
        self.table_widget.setRowCount(len(records))
        for row_index, record in enumerate(records):
            for column_index, value in enumerate(record.to_table_row()):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignCenter)
                self.table_widget.setItem(row_index, column_index, item)
        self.table_widget.resizeColumnsToContents()#после заполнения автоматически подгоняем ширину колонок под содержимое

    def _fill_tree(self, records: list[TrainRecord]) -> None:
        self.tree_widget.clear()
        for record in records:
            root_text = f'Поезд № {record.train_number}'
            root_item = QTreeWidgetItem([root_text, ''])
            root_item.addChild(QTreeWidgetItem(['Станция отправления', record.departure_station]))
            root_item.addChild(QTreeWidgetItem(['Станция прибытия', record.arrival_station]))
            root_item.addChild(
                QTreeWidgetItem(
                    ['Дата и время отправления', record.departure_datetime.strftime('%d.%m.%Y %H:%M')]
                )
            )
            root_item.addChild(
                QTreeWidgetItem(
                    ['Дата и время прибытия', record.arrival_datetime.strftime('%d.%m.%Y %H:%M')]
                )
            )
            root_item.addChild(QTreeWidgetItem(['Время в пути', record.get_travel_time_display()]))
            self.tree_widget.addTopLevelItem(root_item)
            root_item.setExpanded(True)
        self.tree_widget.expandAll()
        self.tree_widget.resizeColumnToContents(0)
        self.tree_widget.resizeColumnToContents(1)

    def show_info_message(self, title: str, message: str) -> None:
        QMessageBox.information(self, title, message)

    def show_error_message(self, title: str, message: str) -> None:
        QMessageBox.critical(self, title, message)

    def set_current_database_path(self, path: str | Path) -> None:
        self.statusBar().showMessage(f'Текущая база данных: {Path(path)}')
