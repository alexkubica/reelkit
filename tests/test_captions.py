import unittest

from PIL import Image, ImageChops

from reelkit.captions import CaptionPainter, build_caption_cues, visual_word_runs


class CaptionTests(unittest.TestCase):
    def test_short_groups_preserve_narration(self):
        scene = {"text": "One two three four five six seven eight"}
        cues = build_caption_cues(scene, 4)
        self.assertEqual([len(c.words) for c in cues], [3, 3, 2])
        self.assertEqual(" ".join(c.text for c in cues), scene["text"])
        self.assertTrue(all(a.end <= b.start for a, b in zip(cues, cues[1:])))

    def test_real_word_boundaries_control_highlighting(self):
        scene = {"text": "שלום AI", "words": [
            {"text": "שלום", "start": 0.2, "end": 0.7},
            {"text": "AI", "start": 0.9, "end": 1.4},
        ]}
        cue = build_caption_cues(scene, 2)[0]
        self.assertEqual(cue.start, 0.2)
        self.assertEqual(cue.words[1].start, 0.9)
        self.assertLessEqual(cue.end, 2)

    def test_bidi_preserves_word_identity_and_latin_order(self):
        hebrew = visual_word_runs(["שלום", "עולם"])
        self.assertEqual([run[0] for run in hebrew], [1, 0])
        self.assertEqual([run[2] for run in hebrew], ["עולם", "שלום"])
        mixed = visual_word_runs(["שלום", "AI", "123"])
        self.assertEqual([run[0] for run in mixed], [1, 2, 0])
        self.assertEqual([run[1] for run in mixed][:2], ["AI", "123"])

    def test_caption_geometry_is_constant_as_word_color_changes(self):
        cue = build_caption_cues({"text": "שלום AI 123"}, 2)[0]
        config = {"size": 32, "position": 0.5, "color": "#ffffff", "highlight": "#99f3c4"}
        painter = CaptionPainter(config, 360, 640)
        for raqm in (painter.raqm, False):
            painter.raqm = raqm
            painter.cache.clear()
            first = painter._stamp(cue, 0)
            second = painter._stamp(cue, 1)
            self.assertEqual(first.size, second.size)
            self.assertEqual(first.getchannel("A").tobytes(), second.getchannel("A").tobytes())
            self.assertNotEqual(first.tobytes(), second.tobytes())
            frame = Image.new("RGB", (360, 640), "#101827")
            before = frame.copy()
            painter.paint(frame, cue, 0.5)
            bounds = ImageChops.difference(before, frame).getbbox()
            self.assertIsNotNone(bounds)
            self.assertLess(abs((bounds[1] + bounds[3]) / 2 - 320), 32)


if __name__ == "__main__":
    unittest.main()
