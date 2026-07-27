from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from train_schedule_app.controllers.main_controller import MainController
from train_schedule_app.repositories.sqlite_train_repository import SQLiteTrainRepository
from train_schedule_app.services.pagination_service import PaginationService
from train_schedule_app.services.train_search_service import TrainSearchService
from train_schedule_app.services.xml_export_service import XmlExportService
from train_schedule_app.services.xml_import_service import XmlImportService
from train_schedule_app.views.main_window import MainWindow


def build_default_database_path() -> Path:
    base_dir = Path(__file__).resolve().parent
    data_dir = base_dir / 'data'
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / 'train_records.db'


def main() -> int:
    application = QApplication(sys.argv)

    main_window = MainWindow()
    repository = SQLiteTrainRepository(build_default_database_path())
    pagination_service = PaginationService()
    search_service = TrainSearchService()
    xml_export_service = XmlExportService()
    xml_import_service = XmlImportService()

    controller = MainController(
        main_window=main_window,
        repository=repository,
        pagination_service=pagination_service,
        search_service=search_service,
        xml_export_service=xml_export_service,
        xml_import_service=xml_import_service,
    )

    main_window.controller = controller
    main_window.show()
    return application.exec()


if __name__ == '__main__':
    raise SystemExit(main())
