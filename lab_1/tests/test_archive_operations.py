import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.user import User
from core.filesystem import FileSystem
from operations.file_operations import touch, write_file, mkdir
from operations.archive_operations import archive, extract


class TestArchiveOperations(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()
        self.fs._init_default_state()
        self.root = self.fs.current_disk.root
        touch(self.fs, "a.txt")
        write_file(self.fs, "a.txt", "AAA")
        touch(self.fs, "b.txt")
        write_file(self.fs, "b.txt", "BBB")

    def test_archive(self):
        archive(self.fs, ["a.txt", "b.txt"], "test.zip")
        self.assertIn("test.zip", self.root.list_entries())
        archive_file = self.root.get_entry("test.zip")
        self.assertEqual(archive_file.name, "test.zip")
        self.assertGreater(len(archive_file.content), 0)

    def test_archive_source_not_found(self):
        with self.assertRaises(FileNotFoundError):
            archive(self.fs, ["missing.txt"], "test.zip")

    def test_archive_source_is_folder(self):
        mkdir(self.fs, "folder")
        with self.assertRaises(IsADirectoryError):
            archive(self.fs, ["folder"], "test.zip")

    def test_extract(self):
        archive(self.fs, ["a.txt", "b.txt"], "test.zip")
        mkdir(self.fs, "dest")
        extract(self.fs, "test.zip", "dest")
        dest_folder = self.root.get_entry("dest")
        self.assertIn("a.txt", dest_folder.list_entries())
        self.assertIn("b.txt", dest_folder.list_entries())
        a = dest_folder.get_entry("a.txt")
        self.assertEqual(a.content, b"AAA")

    def test_extract_archive_not_found(self):
        with self.assertRaises(FileNotFoundError):
            extract(self.fs, "missing.zip", "dest")

    def test_extract_not_a_zip(self):
        touch(self.fs, "notazip.txt")
        with self.assertRaises(ValueError):
            extract(self.fs, "notazip.txt", "dest")