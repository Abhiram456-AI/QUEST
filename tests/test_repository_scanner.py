import unittest
import tempfile
import shutil
from pathlib import Path
from quest.intelligence.repository_scanner import RepositoryScanner, RepositoryMetadata

class TestRepositoryScanner(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_repository_scanner_empty(self):
        scanner = RepositoryScanner(str(self.test_dir))
        result = scanner.scan()
        self.assertIsInstance(result, RepositoryMetadata)
        self.assertEqual(result.total_files, 0)
        self.assertEqual(result.total_loc, 0)
        self.assertEqual(len(result.files), 0)

    def test_repository_scanner_with_files(self):
        py_file = self.test_dir / "main.py"
        py_content = "def test():\n    print('hello')\n"
        py_file.write_text(py_content, encoding="utf-8")

        txt_file = self.test_dir / "info.txt"
        txt_file.write_text("Should be ignored because of extension", encoding="utf-8")

        git_dir = self.test_dir / ".git"
        git_dir.mkdir()
        ignored_py = git_dir / "ignored.py"
        ignored_py.write_text("def ignore():\n    pass\n", encoding="utf-8")

        scanner = RepositoryScanner(str(self.test_dir))
        result = scanner.scan()

        self.assertEqual(result.total_files, 1)
        self.assertEqual(result.total_loc, 2)
        self.assertIn("Python", result.languages)
        self.assertEqual(result.languages["Python"], 1)
        self.assertEqual(len(result.files), 1)
        self.assertEqual(result.files[0]["path"], "main.py")
        self.assertEqual(result.files[0]["language"], "Python")
        self.assertEqual(result.files[0]["lines_of_code"], 2)
