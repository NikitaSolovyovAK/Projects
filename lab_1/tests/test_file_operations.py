import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.user import User
from models.disk import Disk
from models.folder import Folder
from models.file import File
from models.file_format import FileFormat
from core.filesystem import FileSystem
from operations.file_operations import (
    touch, mkdir, write_file, cat, cp, mv, rm
)


class TestFileOperations(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()
        self.fs._init_default_state()
        self.user = self.fs.current_user
        self.disk = self.fs.current_disk
        self.root = self.disk.root

    def test_touch(self):
        touch(self.fs, "test.txt")
        self.assertIn("test.txt", self.root.list_entries())
        entry = self.root.get_entry("test.txt")
        self.assertIsInstance(entry, File)
        self.assertEqual(entry.format, FileFormat.TXT)

    def test_touch_existing_raises(self):
        touch(self.fs, "test.txt")
        with self.assertRaises(FileExistsError):
            touch(self.fs, "test.txt")

    def test_touch_no_permission(self):
        self.root.permissions.owner = 5
        with self.assertRaises(PermissionError):
            touch(self.fs, "no.txt")

    def test_mkdir(self):
        mkdir(self.fs, "newdir")
        self.assertIn("newdir", self.root.list_entries())
        entry = self.root.get_entry("newdir")
        self.assertIsInstance(entry, Folder)

    def test_mkdir_existing_raises(self):
        mkdir(self.fs, "newdir")
        with self.assertRaises(FileExistsError):
            mkdir(self.fs, "newdir")

    def test_write_file(self):
        touch(self.fs, "test.txt")
        write_file(self.fs, "test.txt", "hello")
        entry = self.root.get_entry("test.txt")
        self.assertEqual(entry.content, b"hello")

    def test_write_file_not_found(self):
        with self.assertRaises(FileNotFoundError):
            write_file(self.fs, "missing.txt", "data")

    def test_write_file_is_folder(self):
        mkdir(self.fs, "folder")
        with self.assertRaises(IsADirectoryError):
            write_file(self.fs, "folder", "data")

    def test_cat(self):
        touch(self.fs, "test.txt")
        write_file(self.fs, "test.txt", "hello")
        content = cat(self.fs, "test.txt")
        self.assertEqual(content, "hello")

    def test_cat_not_found(self):
        with self.assertRaises(FileNotFoundError):
            cat(self.fs, "missing.txt")

    def test_cat_is_folder(self):
        mkdir(self.fs, "folder")
        with self.assertRaises(IsADirectoryError):
            cat(self.fs, "folder")

    def test_cp_file_to_folder(self):
        touch(self.fs, "src.txt")
        mkdir(self.fs, "dest")
        cp(self.fs, "src.txt", "dest")
        self.assertIn("src.txt", self.root.get_entry("dest").list_entries())

    def test_cp_file_with_new_name(self):
        touch(self.fs, "src.txt")
        cp(self.fs, "src.txt", "dest.txt")
        self.assertIn("dest.txt", self.root.list_entries())
        self.assertIn("src.txt", self.root.list_entries())

    def test_cp_source_not_found(self):
        with self.assertRaises(FileNotFoundError):
            cp(self.fs, "missing.txt", "dest.txt")

    def test_cp_source_is_folder(self):
        mkdir(self.fs, "folder")
        with self.assertRaises(IsADirectoryError):
            cp(self.fs, "folder", "dest.txt")

    def test_mv_rename(self):
        touch(self.fs, "src.txt")
        mv(self.fs, "src.txt", "dst.txt")
        self.assertIn("dst.txt", self.root.list_entries())
        self.assertNotIn("src.txt", self.root.list_entries())

    def test_mv_move_to_folder(self):
        touch(self.fs, "src.txt")
        mkdir(self.fs, "dest")
        mv(self.fs, "src.txt", "dest")
        self.assertIn("src.txt", self.root.get_entry("dest").list_entries())
        self.assertNotIn("src.txt", self.root.list_entries())

    def test_rm_file(self):
        touch(self.fs, "file.txt")
        rm(self.fs, "file.txt", recursive=False)
        self.assertNotIn("file.txt", self.root.list_entries())

    def test_rm_empty_folder(self):
        mkdir(self.fs, "empty")
        rm(self.fs, "empty", recursive=False)
        self.assertNotIn("empty", self.root.list_entries())

    def test_rm_nonempty_folder_without_recursive(self):
        mkdir(self.fs, "folder")
        self.fs.current_folder = self.fs.resolve_path("folder")
        touch(self.fs, "file.txt")
        self.fs.current_folder = self.root
        with self.assertRaises(IsADirectoryError):
            rm(self.fs, "folder", recursive=False)

    def test_rm_nonempty_folder_with_recursive(self):
        mkdir(self.fs, "folder")
        self.fs.current_folder = self.fs.resolve_path("folder")
        touch(self.fs, "file.txt")
        self.fs.current_folder = self.root
        rm(self.fs, "folder", recursive=True)
        self.assertNotIn("folder", self.root.list_entries())

    def test_rm_root(self):
        with self.assertRaises(PermissionError):
            rm(self.fs, "/", recursive=True)