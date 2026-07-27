import unittest
import sys
import os
from unittest.mock import patch, MagicMock
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.filesystem import FileSystem
from cli.command_line import CLI


class TestCLI(unittest.TestCase):
    def setUp(self):
        self.fs = FileSystem()
        self.fs._init_default_state()
        self.cli = CLI(self.fs)

    @patch('builtins.input', side_effect=['pwd', 'exit'])
    @patch('builtins.print')
    def test_pwd(self, mock_print, mock_input):
        self.cli.run()
        mock_print.assert_any_call('/')

    @patch('builtins.input', side_effect=['ls', 'exit'])
    @patch('builtins.print')
    def test_ls_empty(self, mock_print, mock_input):
        self.cli.run()

    @patch('builtins.input', side_effect=['mkdir test', 'ls', 'exit'])
    @patch('builtins.print')
    def test_mkdir(self, mock_print, mock_input):
        self.cli.run()
        self.assertIn('test', self.fs.current_disk.root.list_entries())

    @patch('builtins.input', side_effect=['cd /', 'exit'])
    @patch('builtins.print')
    def test_cd_root(self, mock_print, mock_input):
        self.cli.run()
        self.assertEqual(self.fs.current_folder, self.fs.current_disk.root)

    @patch('builtins.input', side_effect=['touch file.txt', 'ls', 'exit'])
    @patch('builtins.print')
    def test_touch(self, mock_print, mock_input):
        self.cli.run()
        self.assertIn('file.txt', self.fs.current_folder.list_entries())

    @patch('builtins.input', side_effect=['write file.txt hello', 'cat file.txt', 'exit'])
    @patch('builtins.print')
    def test_write_cat(self, mock_print, mock_input):
        from operations.file_operations import touch
        touch(self.fs, 'file.txt')
        with patch('builtins.input', side_effect=['write file.txt hello', 'cat file.txt', 'exit']):
            self.cli.run()
        entry = self.fs.current_folder.get_entry('file.txt')
        self.assertEqual(entry.content, b'hello')
        mock_print.assert_any_call('hello')

    @patch('builtins.input', side_effect=['cp file.txt file2.txt', 'exit'])
    @patch('builtins.print')
    def test_cp(self, mock_print, mock_input):
        from operations.file_operations import touch
        touch(self.fs, 'file.txt')
        self.cli.run()
        self.assertIn('file2.txt', self.fs.current_folder.list_entries())

    @patch('builtins.input', side_effect=['mv file.txt moved.txt', 'exit'])
    @patch('builtins.print')
    def test_mv(self, mock_print, mock_input):
        from operations.file_operations import touch
        touch(self.fs, 'file.txt')
        self.cli.run()
        self.assertIn('moved.txt', self.fs.current_folder.list_entries())
        self.assertNotIn('file.txt', self.fs.current_folder.list_entries())

    @patch('builtins.input', side_effect=['rm file.txt', 'exit'])
    @patch('builtins.print')
    def test_rm(self, mock_print, mock_input):
        from operations.file_operations import touch
        touch(self.fs, 'file.txt')
        self.cli.run()
        self.assertNotIn('file.txt', self.fs.current_folder.list_entries())

    @patch('builtins.input', side_effect=['chmod 755 file.txt', 'exit'])
    @patch('builtins.print')
    def test_chmod(self, mock_print, mock_input):
        from operations.file_operations import touch
        touch(self.fs, 'file.txt')
        self.cli.run()
        entry = self.fs.current_folder.get_entry('file.txt')
        self.assertEqual(entry.permissions.owner, 7)
        self.assertEqual(entry.permissions.group, 5)
        self.assertEqual(entry.permissions.other, 5)

    @patch('builtins.input', side_effect=['chown admin file.txt', 'exit'])
    @patch('builtins.print')
    def test_chown(self, mock_print, mock_input):
        from operations.file_operations import touch
        touch(self.fs, 'file.txt')
        self.cli.run()

    @patch('builtins.input', side_effect=['lsperm', 'exit'])
    @patch('builtins.print')
    def test_lsperm(self, mock_print, mock_input):
        self.cli.run()
        self.assertTrue(mock_print.called)

    @patch('builtins.input', side_effect=['archive test.zip a.txt b.txt', 'exit'])
    @patch('builtins.print')
    def test_archive(self, mock_print, mock_input):
        from operations.file_operations import touch
        touch(self.fs, 'a.txt')
        touch(self.fs, 'b.txt')
        self.cli.run()
        self.assertIn('test.zip', self.fs.current_folder.list_entries())

    @patch('builtins.input', side_effect=['backup', 'exit'])
    @patch('builtins.print')
    def test_backup(self, mock_print, mock_input):
        self.cli.run()
        self.assertIn('backups', self.fs.current_disk.root.list_entries())

    @patch('builtins.input', side_effect=['organize .', 'exit'])
    @patch('builtins.print')
    def test_organize(self, mock_print, mock_input):
        from operations.file_operations import touch
        touch(self.fs, 'doc.pdf')
        touch(self.fs, 'image.jpg')
        self.cli.run()
        root = self.fs.current_folder
        self.assertIn('Документы', root.list_entries())
        self.assertIn('Изображения', root.list_entries())

    @patch('builtins.input', side_effect=['help', 'exit'])
    @patch('builtins.print')
    def test_help(self, mock_print, mock_input):
        self.cli.run()
        self.assertTrue(mock_print.called)

    @patch('builtins.input', side_effect=['unknown', 'exit'])
    @patch('builtins.print')
    def test_unknown_command(self, mock_print, mock_input):
        self.cli.run()
        mock_print.assert_any_call("Неизвестная команда: unknown. Введите 'help'.")