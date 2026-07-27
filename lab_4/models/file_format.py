from enum import Enum
from typing import Optional
from dataclasses import dataclass


@dataclass
class FormatProperties:
    extension: str
    category: str


class FileFormat(Enum):

    TXT = FormatProperties("txt", "text")
    PDF = FormatProperties("pdf", "document")
    JPG = FormatProperties("jpg", "image")
    ZIP = FormatProperties("zip", "archive")
    PY = FormatProperties("py", "code")
    JSON = FormatProperties("json", "data")
    EXE = FormatProperties("exe", "executable")

    @property
    def extension(self) -> str:
        return self.value.extension

    @property
    def category(self) -> str:
        return self.value.category

    @classmethod
    def from_file(cls, filename: str) -> Optional["FileFormat"]:
        if '.' in filename:
            ext = filename.split('.')[-1].lower()
            for fmt in cls:
                if fmt.extension == ext:
                    return fmt
        return None

    #Возвращение имя папки для огранизации файлов этой категории
    def get_folder_name_for_category(self) -> str:
        folders = {
            "text": "Текстовые файлы",
            "document": "Документы",
            "image": "Изображения",
            "archive": "Архивы",
            "code": "Исходный код",
            "data": "Данные",
            "executable": "Исполняемые файлы"
        }
        return folders.get(self.category, "Другие")