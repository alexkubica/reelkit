import json
from pathlib import Path
import tempfile
import unittest

from reelkit.project import load_project, resolve_project_path


class ProjectValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.path = self.root / "project.json"
        self.project = {"version": 1, "title": "Test reel", "scenes": [{"text": "שלום AI", "duration": 1}]}

    def tearDown(self):
        self.temporary.cleanup()

    def load(self):
        self.path.write_text(json.dumps(self.project, ensure_ascii=False), encoding="utf-8")
        return load_project(self.path)

    def test_defaults_and_ignored_internal_paths(self):
        self.project["scenes"][0]["_audio"] = "/private/example.wav"
        self.project["caption"] = {"_font": "/private/example.ttf"}
        project = self.load()
        self.assertEqual(project["width"], 720)
        self.assertEqual(project["caption"]["position"], 0.5)
        self.assertNotIn("_audio", project["scenes"][0])
        self.assertNotIn("_font", project["caption"])

    def test_traversal_absolute_and_remote_paths_rejected(self):
        for value in ("../outside.png", "/tmp/outside.png", "C:\\outside.png", "C:outside.png", "\\\\server\\share\\image.png", "https://example.org/image.png", "file:asset.png"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                resolve_project_path(self.root, value, "image", must_exist=False)

    def test_symlink_cannot_escape(self):
        with tempfile.TemporaryDirectory() as other:
            target = Path(other) / "image.png"
            target.write_bytes(b"placeholder")
            try:
                (self.root / "linked.png").symlink_to(target)
            except (OSError, NotImplementedError):
                self.skipTest("Symlinks unavailable in this environment")
            with self.assertRaisesRegex(ValueError, "escapes"):
                resolve_project_path(self.root, "linked.png")

    def test_portable_relative_path(self):
        (self.root / "assets").mkdir()
        (self.root / "assets" / "art.png").write_bytes(b"placeholder")
        self.assertEqual(resolve_project_path(self.root, "assets\\art.png"), (self.root / "assets" / "art.png").resolve())

    def test_invalid_dimensions_and_nonfinite_duration(self):
        for key, value in (("width", 719), ("height", -10), ("fps", True), ("width", 9000)):
            with self.subTest(key=key, value=value):
                self.project[key] = value
                with self.assertRaises(ValueError):
                    self.load()
                del self.project[key]
        for duration in (float("nan"), float("inf"), -1):
            self.project["scenes"][0]["duration"] = duration
            with self.assertRaisesRegex(ValueError, "duration"):
                self.load()

    def test_timings_and_text_alignment(self):
        scene = self.project["scenes"][0]
        scene["words"] = [{"text": "שלום", "start": 0.1, "end": 0.5}, {"text": "AI", "start": 0.4, "end": 0.8}]
        with self.assertRaisesRegex(ValueError, "non-overlapping"):
            self.load()
        scene["words"][1]["start"] = 0.5
        self.assertEqual(len(self.load()["scenes"][0]["words"]), 2)
        scene["words"][1]["text"] = "different"
        with self.assertRaisesRegex(ValueError, "match"):
            self.load()

    def test_phrase_and_duplicate_scene_validation(self):
        self.project["scenes"][0]["phrases"] = ["AI שלום"]
        with self.assertRaisesRegex(ValueError, "same order"):
            self.load()
        del self.project["scenes"][0]["phrases"]
        self.project["scenes"] = [{"id": "same", "text": "One"}, {"id": "same", "text": "Two"}]
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.load()


if __name__ == "__main__":
    unittest.main()
