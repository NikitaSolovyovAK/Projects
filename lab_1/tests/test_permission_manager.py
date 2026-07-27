import unittest
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.user import User
from models.disk import Disk
from core.filesystem import FileSystem
from operations.file_operations import touch, mkdir
from operations.permission_manager import chmod, chown, lsperm


class TestPermissionManager(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()
        self.fs._init_default_state()
        self.admin = self.fs.current_user
        self.root = self.fs.current_disk.root
        touch(self.fs, "test.txt")
        self.file = self.root.get_entry("test.txt")

    def test_chmod(self):
        chmod(self.fs, "test.txt", 0o700)
        self.assertEqual(self.file.permissions.owner, 7)
        self.assertEqual(self.file.permissions.group, 0)
        self.assertEqual(self.file.permissions.other, 0)

    def test_chmod_not_owner(self):
        other_user = User("other")
        self.fs.users[other_user.user_id] = other_user
        self.fs.current_user = other_user
        with self.assertRaises(PermissionError):
            chmod(self.fs, "test.txt", 0o700)

    def test_chmod_admin_can_change(self):
        other_user = User("other")
        self.fs.users[other_user.user_id] = other_user
        self.fs.current_user = other_user
        self.fs.current_user = self.admin
        chmod(self.fs, "test.txt", 0o700)

    def test_chmod_path_not_found(self):
        with self.assertRaises(FileNotFoundError):
            chmod(self.fs, "missing", 0o755)

    def test_chown(self):
        new_user = User("new")
        self.fs.users[new_user.user_id] = new_user
        chown(self.fs, "test.txt", "new")
        self.assertEqual(self.file.owner, new_user)

    def test_chown_not_admin(self):
        other_user = User("other")
        self.fs.users[other_user.user_id] = other_user
        self.fs.current_user = other_user
        with self.assertRaises(PermissionError):
            chown(self.fs, "test.txt", "new")

    def test_chown_user_not_found(self):
        with self.assertRaises(ValueError):
            chown(self.fs, "test.txt", "nonexistent")

    def test_lsperm(self):
        s = lsperm(self.fs, "test.txt")
        self.assertIn("test.txt", s)
        self.assertIn("admin", s)

    def test_lsperm_not_found(self):
        with self.assertRaises(FileNotFoundError):
            lsperm(self.fs, "missing")