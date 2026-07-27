import unittest
import sys
import os
import tempfile
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.user import User
from models.disk import Disk
from core.filesystem import FileSystem
from operations.file_operations import touch, mkdir


class TestFileSystem(unittest.TestCase):
    def setUp(self):
        self.temp_state = tempfile.NamedTemporaryFile(delete=False, suffix=".json")
        self.temp_state.close()
        self.fs = FileSystem(state_file=self.temp_state.name)

    def tearDown(self):
        try:
            os.unlink(self.temp_state.name)
        except FileNotFoundError:
            pass

    def test_init_default_state(self):
        self.fs._init_default_state()
        self.assertEqual(len(self.fs.users), 1)
        self.assertEqual(len(self.fs.disks), 1)
        self.assertIsNotNone(self.fs.current_user)
        self.assertIsNotNone(self.fs.current_disk)
        self.assertIsNotNone(self.fs.current_folder)

    def test_save_and_load(self):
        self.fs._init_default_state()
        mkdir(self.fs, "test")
        self.fs.current_folder = self.fs.resolve_path("test")
        touch(self.fs, "file.txt")
        self.fs.current_folder = self.fs.current_disk.root
        self.fs.save()
        fs2 = FileSystem(state_file=self.temp_state.name)
        loaded = fs2.load()
        self.assertTrue(loaded)
        self.assertEqual(len(fs2.users), 1)
        self.assertEqual(len(fs2.disks), 1)
        disk = fs2.disks[0]
        self.assertIn("test", disk.root.list_entries())
        test_folder = disk.root.get_entry("test")
        self.assertIn("file.txt", test_folder.list_entries())

    def test_load_nonexistent(self):
        os.unlink(self.temp_state.name)
        fs = FileSystem(state_file=self.temp_state.name)
        result = fs.load()
        self.assertFalse(result)

    def test_load_corrupted(self):
        with open(self.temp_state.name, 'w') as f:
            f.write("not json")
        fs = FileSystem(state_file=self.temp_state.name)
        result = fs.load()
        self.assertFalse(result)

    def test_resolve_path(self):
        self.fs._init_default_state()
        mkdir(self.fs, "folder")
        self.fs.current_folder = self.fs.resolve_path("folder")
        touch(self.fs, "file.txt")
        self.fs.current_folder = self.fs.current_disk.root
        entry = self.fs.resolve_path("/folder/file.txt")
        self.assertIsNotNone(entry)
        self.assertEqual(entry.name, "file.txt")
        self.fs.current_folder = self.fs.resolve_path("folder")
        entry = self.fs.resolve_path("file.txt")
        self.assertIsNotNone(entry)
        entry = self.fs.resolve_path("/missing")
        self.assertIsNone(entry)