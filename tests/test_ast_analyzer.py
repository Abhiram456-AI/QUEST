import unittest
import tempfile
import shutil
from pathlib import Path
from quest.intelligence.ast_analyzer import ASTAnalyzer, ASTResult

class TestASTAnalyzer(unittest.TestCase):
    def setUp(self):
        self.test_dir = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_ast_analyzer_valid_file(self):
        code = (
            "import os\n"
            "from sys import argv\n\n"
            "def dummy_function(a, b):\n"
            "    return a + b\n\n"
            "class DummyClass(object):\n"
            "    def __init__(self):\n"
            "        pass\n"
            "    def method_one(self, x):\n"
            "        dummy_function(x, 1)\n"
        )
        temp_file = self.test_dir / "sample.py"
        temp_file.write_text(code, encoding="utf-8")

        analyzer = ASTAnalyzer()
        result = analyzer.analyze_file(str(temp_file))

        self.assertIsInstance(result, ASTResult)
        self.assertEqual(result.file_path, str(temp_file))
        self.assertIn("os", result.imports)
        self.assertIn("sys", result.imports)

        # Check functions
        self.assertEqual(len(result.functions), 3)  # dummy_function, __init__, method_one (as functions are visited globally)
        func_names = [f["name"] for f in result.functions]
        self.assertIn("dummy_function", func_names)
        self.assertIn("__init__", func_names)
        self.assertIn("method_one", func_names)

        # Check classes
        self.assertEqual(len(result.classes), 1)
        self.assertEqual(result.classes[0]["name"], "DummyClass")
        self.assertIn("__init__", result.classes[0]["methods"])
        self.assertIn("method_one", result.classes[0]["methods"])
        self.assertIn("object", result.classes[0]["inheritance"])

    def test_ast_analyzer_invalid_syntax(self):
        code = "def invalid_syntax_function(\n"
        temp_file = self.test_dir / "invalid.py"
        temp_file.write_text(code, encoding="utf-8")

        analyzer = ASTAnalyzer()
        with self.assertRaises(ValueError):
            analyzer.analyze_file(str(temp_file))
