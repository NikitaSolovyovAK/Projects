import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.user import User
from core.filesystem import FileSystem
from operations.file_operations import touch, mkdir
from operations.organization import organize


class TestOrganization(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()
        self.fs._init_default_state()
        self.root = self.fs.current_disk.root
        mkdir(self.fs, "source")
        self.source = self.root.get_entry("source")
        self.fs.current_folder = self.source
        touch(self.fs, "doc.pdf")
        touch(self.fs, "image.jpg")
        touch(self.fs, "script.py")
        touch(self.fs, "data.json")
        touch(self.fs, "archive.zip")
        self.fs.current_folder = self.root

    def test_organize(self):
        organize(self.fs, "source")
        expected_cats = ["Документы", "Изображения", "Исходный код", "Данные", "Архивы"]
        for cat in expected_cats:
            self.assertIn(cat, self.source.list_entries())
        docs = self.source.get_entry("Документы")
        self.assertIn("doc.pdf", docs.list_entries())
        images = self.source.get_entry("Изображения")
        self.assertIn("image.jpg", images.list_entries())
        code = self.source.get_entry("Исходный код")
        self.assertIn("script.py", code.list_entries())
        data = self.source.get_entry("Данные")
        self.assertIn("data.json", data.list_entries())
        arch = self.source.get_entry("Архивы")
        self.assertIn("archive.zip", arch.list_entries())

    def test_organize_non_folder(self):
        touch(self.fs, "file.txt")
        with self.assertRaises(NotADirectoryError):
            organize(self.fs, "file.txt")

    def test_organize_not_found(self):
        with self.assertRaises(NotADirectoryError):
            organize(self.fs, "missing")