from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QMessageBox

from train_schedule_app.models.search_criteria import SearchCriteria
from train_schedule_app.models.train_record import TrainValidationError
from train_schedule_app.repositories.sqlite_train_repository import SQLiteTrainRepository
from train_schedule_app.repositories.train_repository import TrainRepository
from train_schedule_app.services.pagination_service import PaginationService
from train_schedule_app.services.train_search_service import TrainSearchService
from train_schedule_app.services.xml_export_service import XmlExportService
from train_schedule_app.services.xml_import_service import XmlImportService
from train_schedule_app.views.add_train_dialog import AddTrainDialog
from train_schedule_app.views.delete_dialog import DeleteDialog
from train_schedule_app.views.main_window import MainWindow
from train_schedule_app.views.search_dialog import SearchDialog


class MainController:
    def __init__(
        self,
        main_window: MainWindow,
        repository: TrainRepository,
        pagination_service: PaginationService,
        search_service: TrainSearchService,
        xml_export_service: XmlExportService,
        xml_import_service: XmlImportService,
    ) -> None:
        self.main_window = main_window
        self.repository = repository
        self.pagination_service = pagination_service
        self.search_service = search_service
        self.xml_export_service = xml_export_service
        self.xml_import_service = xml_import_service

        self.main_page_number: int = 1
        self.search_page_number: int = 1
        self.search_results = []
        self.search_dialog: SearchDialog | None = None
        self.delete_dialog: DeleteDialog | None = None

        self._connect_main_window_signals()
        self._refresh_main_view(reset_page=True)
        if isinstance(self.repository, SQLiteTrainRepository):
            self.main_window.set_current_database_path(self.repository.database_path)

    def _connect_main_window_signals(self) -> None:
        self.main_window.add_requested.connect(self.open_add_dialog)
        self.main_window.search_requested.connect(self.open_search_dialog)
        self.main_window.delete_requested.connect(self.open_delete_dialog)
        self.main_window.save_xml_requested.connect(self.save_to_xml)
        self.main_window.load_xml_requested.connect(self.load_from_xml)
        self.main_window.open_database_requested.connect(self.open_database)
        self.main_window.save_database_as_requested.connect(self.save_database_as)

        pagination_widget = self.main_window.pagination_widget
        pagination_widget.first_requested.connect(self._go_to_first_main_page)
        pagination_widget.previous_requested.connect(self._go_to_previous_main_page)
        pagination_widget.next_requested.connect(self._go_to_next_main_page)
        pagination_widget.last_requested.connect(self._go_to_last_main_page)
        pagination_widget.page_size_changed.connect(self._main_page_size_changed)

    def open_add_dialog(self) -> None:
        dialog = AddTrainDialog(self.main_window)
        if dialog.exec() != dialog.Accepted:
            return
        try:
            record = dialog.get_record()
            self.repository.insert(record)
            self._refresh_main_view(reset_page=False)
            self.main_window.show_info_message('Успех', 'Запись успешно добавлена.')
        except TrainValidationError as error:
            self.main_window.show_error_message('Ошибка валидации', str(error))
        except Exception as error:
            self.main_window.show_error_message('Ошибка', f'Не удалось добавить запись: {error}')

    def open_search_dialog(self) -> None:
        if self.search_dialog is None:
            self.search_dialog = SearchDialog(self.main_window)
            self.search_dialog.search_requested.connect(self._perform_search)
            pagination_widget = self.search_dialog.pagination_widget
            pagination_widget.first_requested.connect(self._go_to_first_search_page)
            pagination_widget.previous_requested.connect(self._go_to_previous_search_page)
            pagination_widget.next_requested.connect(self._go_to_next_search_page)
            pagination_widget.last_requested.connect(self._go_to_last_search_page)
            pagination_widget.page_size_changed.connect(self._search_page_size_changed)
        self.search_results = []
        self.search_page_number = 1
        self.search_dialog.show_results([], 1, 1, 0)
        self.search_dialog.show()
        self.search_dialog.raise_()
        self.search_dialog.activateWindow()

    def open_delete_dialog(self) -> None:
        if self.delete_dialog is None:
            self.delete_dialog = DeleteDialog(self.main_window)
            self.delete_dialog.delete_requested.connect(self._perform_delete)
        self.delete_dialog.show()
        self.delete_dialog.raise_()
        self.delete_dialog.activateWindow()

    def _perform_search(self, criteria: SearchCriteria) -> None:
        all_records = self.repository.get_all()
        self.search_results = self.search_service.search(all_records, criteria)
        self.search_page_number = 1
        self._refresh_search_view()

    def _perform_delete(self, criteria: SearchCriteria) -> None:
        all_records = self.repository.get_all()
        records_to_delete = self.search_service.search(all_records, criteria)
        record_ids = [record.record_id for record in records_to_delete if record.record_id is not None]

        if not record_ids:
            self.main_window.show_info_message('Удаление', 'Подходящие записи не найдены.')
            return

        confirmation = QMessageBox.question(
            self.main_window,
            'Подтверждение удаления',
            f'Будет удалено записей: {len(record_ids)}. Продолжить?',
        )
        if confirmation != QMessageBox.StandardButton.Yes:
            return

        deleted_count = self.repository.delete_by_ids(record_ids)
        self._refresh_main_view(reset_page=False)
        self.main_window.show_info_message(
            'Удаление',
            f'Удалено записей: {deleted_count}.',
        )

    def save_to_xml(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            'Сохранить XML-файл',
            '',
            'XML files (*.xml)',
        )
        if not file_path:
            return
        try:
            records = self.repository.get_all()
            self.xml_export_service.export(file_path, records)
            self.main_window.show_info_message('Сохранение XML', 'Файл успешно сохранён.')
        except Exception as error:
            self.main_window.show_error_message('Ошибка', f'Не удалось сохранить XML: {error}')

    def load_from_xml(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            'Загрузить XML-файл',
            '',
            'XML files (*.xml)',
        )
        if not file_path:
            return
        try:
            records = self.xml_import_service.import_records(file_path)
            self.repository.replace_all(records)
            self._refresh_main_view(reset_page=True)
            self.main_window.show_info_message('Загрузка XML', 'Данные успешно загружены в базу данных.')
        except Exception as error:
            self.main_window.show_error_message('Ошибка', f'Не удалось загрузить XML: {error}')

    def open_database(self) -> None:
        file_path, _ = QFileDialog.getOpenFileName(
            self.main_window,
            'Открыть базу данных SQLite',
            '',
            'SQLite database (*.db *.sqlite);;All files (*)',
        )
        if not file_path:
            return
        self.repository = SQLiteTrainRepository(file_path)
        self.main_window.set_current_database_path(file_path)
        self._refresh_main_view(reset_page=True)

    def save_database_as(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(
            self.main_window,
            'Сохранить базу данных как',
            '',
            'SQLite database (*.db *.sqlite);;All files (*)',
        )
        if not file_path:
            return
        try:
            records = self.repository.get_all()
            new_repository = SQLiteTrainRepository(file_path)
            new_repository.replace_all(records)
            self.repository = new_repository
            self.main_window.set_current_database_path(file_path)
            self._refresh_main_view(reset_page=False)
            self.main_window.show_info_message('База данных', 'База данных успешно сохранена.')
        except Exception as error:
            self.main_window.show_error_message('Ошибка', f'Не удалось сохранить базу данных: {error}')

    def _refresh_main_view(self, reset_page: bool) -> None:
        all_records = self.repository.get_all()
        if reset_page:
            self.main_page_number = 1
        page_size = self.main_window.pagination_widget.current_page_size()
        pagination_result = self.pagination_service.paginate(
            all_records,
            self.main_page_number,
            page_size,
        )
        self.main_page_number = pagination_result.page_number
        self.main_window.show_records(
            records=pagination_result.items,
            page_number=pagination_result.page_number,
            total_pages=pagination_result.total_pages,
            total_items=pagination_result.total_items,
        )

    def _refresh_search_view(self) -> None:
        if self.search_dialog is None:
            return
        page_size = self.search_dialog.current_page_size()
        pagination_result = self.pagination_service.paginate(
            self.search_results,
            self.search_page_number,
            page_size,
        )
        self.search_page_number = pagination_result.page_number
        self.search_dialog.show_results(
            records=pagination_result.items,
            page_number=pagination_result.page_number,
            total_pages=pagination_result.total_pages,
            total_items=pagination_result.total_items,
        )

    def _go_to_first_main_page(self) -> None:
        self.main_page_number = 1
        self._refresh_main_view(reset_page=False)

    def _go_to_previous_main_page(self) -> None:
        self.main_page_number -= 1
        self._refresh_main_view(reset_page=False)

    def _go_to_next_main_page(self) -> None:
        self.main_page_number += 1
        self._refresh_main_view(reset_page=False)

    def _go_to_last_main_page(self) -> None:
        all_records = self.repository.get_all()
        page_size = self.main_window.pagination_widget.current_page_size()
        result = self.pagination_service.paginate(all_records, 10**9, page_size)
        self.main_page_number = result.total_pages
        self._refresh_main_view(reset_page=False)

    def _main_page_size_changed(self, _: int) -> None:
        self.main_page_number = 1
        self._refresh_main_view(reset_page=False)

    def _go_to_first_search_page(self) -> None:
        self.search_page_number = 1
        self._refresh_search_view()

    def _go_to_previous_search_page(self) -> None:
        self.search_page_number -= 1
        self._refresh_search_view()

    def _go_to_next_search_page(self) -> None:
        self.search_page_number += 1
        self._refresh_search_view()

    def _go_to_last_search_page(self) -> None:
        if self.search_dialog is None:
            return
        page_size = self.search_dialog.current_page_size()
        result = self.pagination_service.paginate(self.search_results, 10**9, page_size)
        self.search_page_number = result.total_pages
        self._refresh_search_view()

    def _search_page_size_changed(self, _: int) -> None:
        self.search_page_number = 1
        self._refresh_search_view()
