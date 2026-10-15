from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from reelkit.cli import initialize, main
from reelkit.project import load_project


class CommandLineTests(unittest.TestCase):
    def test_init_is_self_contained_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as directory:
            project = initialize(Path(directory) / "example", language="he")
            before = project.read_bytes()
            loaded = load_project(project)
            self.assertGreaterEqual(len(loaded["scenes"]), 2)
            self.assertTrue(all(scene.get("_image").is_file() for scene in loaded["scenes"]))
            with self.assertRaisesRegex(ValueError, "never overwrites"):
                initialize(project.parent)
            self.assertEqual(project.read_bytes(), before)

    def test_init_refuses_unrelated_existing_files(self):
        with tempfile.TemporaryDirectory() as directory:
            sentinel = Path(directory) / "keep.txt"
            sentinel.write_text("Keep this", encoding="utf-8")
            with self.assertRaises(ValueError):
                initialize(directory)
            self.assertEqual(sentinel.read_text(encoding="utf-8"), "Keep this")
            self.assertEqual(list(Path(directory).iterdir()), [sentinel])

    def test_default_render_location_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / "project.json"
            project.write_text(json.dumps({"version": 1, "width": 96, "height": 160, "fps": 4,
                                           "caption": {"size": 12}, "scenes": [{"text": "Hello AI", "duration": 0.5}]}), encoding="utf-8")
            output = io.StringIO()
            with redirect_stdout(output):
                self.assertEqual(main(["validate", str(project)]), 0)
                self.assertEqual(main(["render", str(project), "--draft"]), 0)
            self.assertIn("Valid project", output.getvalue())
            self.assertTrue((root / "build" / "reel.mp4").is_file())
            self.assertTrue((root / "build" / "reel.srt").is_file())

    def test_invalid_project_has_actionable_error_without_traceback(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text('{"version":1,"scenes":[]}', encoding="utf-8")
            error = io.StringIO()
            with redirect_stderr(error):
                self.assertEqual(main(["validate", str(path)]), 1)
            self.assertIn("scenes must contain", error.getvalue())
            self.assertNotIn("Traceback", error.getvalue())


if __name__ == "__main__":
    unittest.main()
