import unittest
import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.user import User
from models.folder import Folder
from core.filesystem import FileSystem
from operations.file_operations import touch, write_file, mkdir, rm
from operations.backup_operations import backup, restore


class TestBackupOperations(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()
        self.fs._init_default_state()
        self.root = self.fs.current_disk.root
        mkdir(self.fs, "docs")
        self.fs.current_folder = self.fs.resolve_path("docs")
        touch(self.fs, "note.txt")
        write_file(self.fs, "note.txt", "important")
        self.fs.current_folder = self.root

    def test_backup(self):
        backup_file = backup(self.fs)
        self.assertIn("backups", self.root.list_entries())
        backups = self.root.get_entry("backups")
        self.assertIsInstance(backups, Folder)
        self.assertEqual(len(backups.list_entries()), 1)
        bf = backups.get_entry(backups.list_entries()[0])
        self.assertEqual(bf.format.name, "JSON")

    def test_backup_with_name(self):
        backup(self.fs, "mybackup")
        backups = self.root.get_entry("backups")
        self.assertIn("mybackup.json", backups.list_entries())


    def test_restore_backup_not_found(self):
        with self.assertRaises(FileNotFoundError):
            restore(self.fs, "nonexistent.json")

    def test_restore_corrupted_backup(self):
        backup(self.fs, "good")
        backups = self.root.get_entry("backups")
        bad_file = backups.get_entry("good.json")
        bad_file.content = b"not json"
        with self.assertRaises(ValueError):
            restore(self.fs, "good.json")