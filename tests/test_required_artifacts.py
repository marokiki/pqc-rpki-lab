import tempfile
import unittest
from pathlib import Path

from tools.check_required_artifacts import (
    REQUIRED_FILES,
    REQUIRED_NONEMPTY_DIRECTORIES,
    find_missing,
)


class RequiredArtifactsTest(unittest.TestCase):
    def test_complete_tree_has_no_missing_artifacts(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for path in REQUIRED_FILES:
                target = root / path
                target.parent.mkdir(parents=True, exist_ok=True)
                target.write_text("fixture\n")
            for path in REQUIRED_NONEMPTY_DIRECTORIES:
                directory = root / path
                directory.mkdir(parents=True, exist_ok=True)
                if not any(item.is_file() for item in directory.rglob("*")):
                    (directory / ".fixture").write_text("fixture\n")
            self.assertEqual(find_missing(root), [])

    def test_missing_file_is_reported(self):
        with tempfile.TemporaryDirectory() as name:
            missing = find_missing(Path(name))
        self.assertIn("README.md", missing)
        self.assertIn("results/ (missing or empty)", missing)


if __name__ == "__main__":
    unittest.main()
