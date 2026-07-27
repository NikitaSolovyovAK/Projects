import unittest
from datetime import datetime
import tempfile
import os
import json

import sys
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models.user import User
from models.permission import Permissions
from models.file_format import FileFormat
from models.filesystem_entry import FileSystemEntry
from models.file import File
from models.folder import Folder
from models.disk import Disk


class TestUser(unittest.TestCase):
    def setUp(self):
        self.user = User("testuser")

    def test_user_creation(self):
        self.assertEqual(self.user.username, "testuser")
        self.assertIsNotNone(self.user.user_id)
        self.assertIn("users", self.user.groups)
        self.assertTrue(self.user.permissions["read_own_files"])

    def test_add_to_group(self):
        self.user.add_to_group("staff")
        self.assertIn("staff", self.user.groups)

    def test_remove_from_group(self):
        self.user.add_to_group("staff")
        self.user.remove_from_group("staff")
        self.assertNotIn("staff", self.user.groups)

    def test_set_permission(self):
        self.user.set_permission("test_perm", True)
        self.assertTrue(self.user.permissions["test_perm"])

    def test_is_in_group(self):
        self.assertTrue(self.user.is_in_group("users"))
        self.assertFalse(self.user.is_in_group("admin"))

    def test_to_dict_from_dict(self):
        self.user.add_to_group("staff")
        self.user.set_permission("extra", False)
        data = self.user.to_dict()
        new_user = User.from_dict(data)
        self.assertEqual(self.user.username, new_user.username)
        self.assertEqual(self.user.user_id, new_user.user_id)
        self.assertEqual(self.user.groups, new_user.groups)
        self.assertEqual(self.user.permissions, new_user.permissions)


class TestPermissions(unittest.TestCase):
    def setUp(self):
        self.user = User("owner")
        self.other_user = User("other")
        self.entry = None

    def test_default_permissions(self):
        p = Permissions()
        self.assertEqual(p.owner, 7)
        self.assertEqual(p.group, 5)
        self.assertEqual(p.other, 5)

    def test_setters_validation(self):
        p = Permissions()
        with self.assertRaises(ValueError):
            p.owner = 8
        with self.assertRaises(ValueError):
            p.group = -1
        with self.assertRaises(ValueError):
            p.other = 9

    def test_can_read_write_execute(self):
        owner = User("owner")
        f = File("test.txt", owner, FileFormat.TXT, content="hello")
        self.assertTrue(f.permissions.can_read(owner, f))
        self.assertTrue(f.permissions.can_write(owner, f))
        self.assertTrue(f.permissions.can_execute(owner, f))
        other = User("other")
        self.assertTrue(f.permissions.can_read(other, f))
        self.assertFalse(f.permissions.can_write(other, f))
        self.assertTrue(f.permissions.can_execute(other, f))

    def test_to_dict_from_dict(self):
        p = Permissions(owner=6, group=4, other=0)
        data = p.to_dict()
        p2 = Permissions.from_dict(data)
        self.assertEqual(p2.owner, 6)
        self.assertEqual(p2.group, 4)
        self.assertEqual(p2.other, 0)

    def test_str_repr(self):
        p = Permissions(owner=7, group=5, other=5)
        self.assertEqual(str(p), "rwxr-xr-x")
        self.assertEqual(repr(p), "Permissions(owner=7, group=5, other=5)")


class TestFileFormat(unittest.TestCase):
    def test_from_file(self):
        fmt = FileFormat.from_file("test.txt")
        self.assertEqual(fmt, FileFormat.TXT)
        fmt = FileFormat.from_file("unknown.xyz")
        self.assertIsNone(fmt)

    def test_properties(self):
        fmt = FileFormat.TXT
        self.assertEqual(fmt.extension, "txt")
        self.assertEqual(fmt.category, "text")
        self.assertEqual(fmt.get_folder_name_for_category(), "Текстовые файлы")

    def test_all_formats_exist(self):
        self.assertIsNotNone(FileFormat.TXT)
        self.assertIsNotNone(FileFormat.PDF)
        self.assertIsNotNone(FileFormat.JPG)
        self.assertIsNotNone(FileFormat.ZIP)
        self.assertIsNotNone(FileFormat.PY)
        self.assertIsNotNone(FileFormat.JSON)
        self.assertIsNotNone(FileFormat.EXE)


class TestFileSystemEntry(unittest.TestCase):
    def setUp(self):
        self.user = User("owner")
        self.file = File("test.txt", self.user, FileFormat.TXT, content="data")

    def test_properties(self):
        self.assertEqual(self.file.name, "test.txt")
        self.assertEqual(self.file.owner, self.user)
        self.assertEqual(self.file.group, "users")
        self.assertIsInstance(self.file.permissions, Permissions)
        self.assertIsNone(self.file.parent)

    def test_setters(self):
        new_user = User("new")
        self.file.name = "new.txt"
        self.assertEqual(self.file.name, "new.txt")
        self.file.owner = new_user
        self.assertEqual(self.file.owner, new_user)
        self.file.group = "staff"
        self.assertEqual(self.file.group, "staff")
        new_perm = Permissions(owner=0)
        self.file.permissions = new_perm
        self.assertEqual(self.file.permissions.owner, 0)

    def test_get_path_root(self):
        self.assertEqual(self.file.get_path(), "/")

    def test_get_path_with_parent(self):
        folder = Folder("folder", self.user)
        folder.add_entry(self.file)
        self.assertEqual(self.file.get_path(), "/folder/test.txt")

    def test_disk_property(self):
        disk = Disk("C:", 1000)
        disk.format(self.user)
        root = disk.root
        root.add_entry(self.file)
        self.assertEqual(self.file.disk, disk)

    def test_update_modified(self):
        old = self.file.modified_at
        self.file.name = "newname.txt"
        self.assertGreater(self.file.modified_at, old)


class TestFile(unittest.TestCase):
    def setUp(self):
        self.user = User("owner")
        self.file = File("test.txt", self.user, FileFormat.TXT, content="hello")

    def test_content(self):
        self.assertEqual(self.file.content, b"hello")
        self.file.content = "world"
        self.assertEqual(self.file.content, b"world")
        self.file.content = b"bytes"
        self.assertEqual(self.file.content, b"bytes")

    def test_get_size(self):
        self.assertEqual(self.file.get_size(), 5)

    def test_format(self):
        self.assertEqual(self.file.format, FileFormat.TXT)

    def test_to_dict_from_dict(self):
        data = self.file.to_dict()
        users_map = {self.user.user_id: self.user}
        new_file = File.from_dict(data, users_map)
        self.assertEqual(new_file.name, self.file.name)
        self.assertEqual(new_file.owner, self.file.owner)
        self.assertEqual(new_file.format, self.file.format)
        self.assertEqual(new_file.content, self.file.content)


class TestFolder(unittest.TestCase):
    def setUp(self):
        self.user = User("owner")
        self.folder = Folder("test", self.user)
        self.file = File("file.txt", self.user, FileFormat.TXT, content="data")

    def test_add_entry(self):
        self.folder.add_entry(self.file)
        self.assertIn("file.txt", self.folder.list_entries())
        self.assertEqual(self.file.parent, self.folder)

    def test_add_existing_raises(self):
        self.folder.add_entry(self.file)
        with self.assertRaises(FileExistsError):
            self.folder.add_entry(self.file)

    def test_get_entry(self):
        self.folder.add_entry(self.file)
        entry = self.folder.get_entry("file.txt")
        self.assertEqual(entry, self.file)

    def test_get_entry_not_found(self):
        with self.assertRaises(FileNotFoundError):
            self.folder.get_entry("missing")

    def test_remove_entry(self):
        self.folder.add_entry(self.file)
        self.folder.remove_entry("file.txt")
        self.assertNotIn("file.txt", self.folder.list_entries())
        self.assertIsNone(self.file.parent)

    def test_get_size(self):
        self.folder.add_entry(self.file)
        self.assertEqual(self.folder.get_size(), 4)

    def test_get_files(self):
        self.folder.add_entry(self.file)
        subfolder = Folder("sub", self.user)
        self.folder.add_entry(subfolder)
        files = self.folder.get_files()
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0], self.file)

    def test_to_dict_from_dict(self):
        self.folder.add_entry(self.file)
        data = self.folder.to_dict()
        users_map = {self.user.user_id: self.user}
        new_folder = Folder.from_dict(data, users_map)
        self.assertEqual(new_folder.name, self.folder.name)
        self.assertEqual(len(new_folder.list_entries()), 1)
        child = new_folder.get_entry("file.txt")
        self.assertIsInstance(child, File)
        self.assertEqual(child.content, b"data")


class TestDisk(unittest.TestCase):
    def setUp(self):
        self.user = User("admin")
        self.disk = Disk("C:", 10000)
        self.disk.format(self.user)

    def test_init(self):
        self.assertEqual(self.disk.name, "C:")
        self.assertEqual(self.disk.total_space, 10000)
        self.assertEqual(self.disk.free_space, 10000)
        self.assertIsNotNone(self.disk.disk_id)

    def test_format(self):
        self.assertIsNotNone(self.disk.root)
        self.assertEqual(self.disk.root.name, "/")
        self.assertEqual(self.disk.root.owner, self.user)

    def test_update_free_space(self):
        self.disk.update_free_space()
        self.assertEqual(self.disk.free_space, 10000)
        file = File("test.txt", self.user, FileFormat.TXT, content="a" * 100)
        self.disk.root.add_entry(file)
        self.disk.update_free_space()
        self.assertEqual(self.disk.free_space, 10000 - 100)

    def test_resolve_path_absolute(self):
        file = File("test.txt", self.user, FileFormat.TXT)
        self.disk.root.add_entry(file)
        result = self.disk.resolve_path("/test.txt", self.disk.root)
        self.assertEqual(result, file)

    def test_resolve_path_relative(self):
        folder = Folder("sub", self.user)
        self.disk.root.add_entry(folder)
        file = File("test.txt", self.user, FileFormat.TXT)
        folder.add_entry(file)
        result = self.disk.resolve_path("sub/test.txt", self.disk.root)
        self.assertEqual(result, file)

    def test_resolve_path_not_found(self):
        result = self.disk.resolve_path("/missing", self.disk.root)
        self.assertIsNone(result)

    def test_resolve_path_dot_dot(self):
        folder = Folder("sub", self.user)
        self.disk.root.add_entry(folder)
        result = self.disk.resolve_path("sub/..", self.disk.root)
        self.assertEqual(result, self.disk.root)

    def test_to_dict_from_dict(self):
        file = File("test.txt", self.user, FileFormat.TXT, content="data")
        self.disk.root.add_entry(file)
        data = self.disk.to_dict()
        users_map = {self.user.user_id: self.user}
        new_disk = Disk.from_dict(data, users_map)
        self.assertEqual(new_disk.name, self.disk.name)
        self.assertEqual(new_disk.total_space, self.disk.total_space)
        self.assertEqual(new_disk.free_space, self.disk.free_space)
        root = new_disk.root
        self.assertEqual(root.name, "/")
        self.assertIn("test.txt", root.list_entries())
        restored_file = root.get_entry("test.txt")
        self.assertEqual(restored_file.content, b"data")