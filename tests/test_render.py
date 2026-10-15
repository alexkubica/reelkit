import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch
import wave

from PIL import Image

from reelkit.media import audio_duration, ffmpeg_executable, write_audio_track
from reelkit.render import render_project


class RenderIntegrationTests(unittest.TestCase):
    def test_local_playlist_cannot_trigger_nested_network_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            playlist = root / "local-audio.m3u8"
            playlist.write_text("#EXTM3U\n#EXT-X-TARGETDURATION:1\n#EXT-X-MEDIA-SEQUENCE:0\n#EXTINF:1,\nhttps://127.0.0.1:9/private.ts\n#EXT-X-ENDLIST\n", encoding="utf-8")
            with patch("reelkit.media.subprocess.run", wraps=subprocess.run) as command:
                with self.assertRaisesRegex(ValueError, "valid WAV"):
                    audio_duration(playlist)
                arguments = command.call_args.args[0]
                self.assertEqual(arguments[arguments.index("-protocol_whitelist") + 1], "file,pipe")
                self.assertIn("-format_whitelist", arguments)
            with self.assertRaisesRegex(ValueError, "not on whitelist"):
                write_audio_track([{"id": "malicious", "_audio": playlist}], [1], root / "track.wav")

    def test_encode_two_frames_and_export_subtitles(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            Image.new("RGB", (96, 160), "#304050").save(root / "art.png")
            project = {"version": 1, "width": 96, "height": 160, "fps": 4,
                       "caption": {"size": 12}, "scenes": [{"id": "test", "image": "art.png", "text": "שלום AI", "duration": 0.5}]}
            (root / "project.json").write_text(json.dumps(project), encoding="utf-8")
            result = render_project(root / "project.json", root / "reel.mp4")
            self.assertTrue(result.is_file())
            self.assertIn("שלום AI", result.with_suffix(".srt").read_text(encoding="utf-8"))
            decoded = subprocess.run([ffmpeg_executable(), "-v", "error", "-i", str(result), "-f", "rawvideo", "-pix_fmt", "rgb24", "pipe:1"],
                                     stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            self.assertEqual(len(decoded.stdout), 96 * 160 * 3 * 2)

    def test_narration_and_silent_scenes_share_timeline(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with wave.open(str(root / "voice.wav"), "wb") as audio:
                audio.setnchannels(1)
                audio.setsampwidth(2)
                audio.setframerate(24000)
                audio.writeframes(b"\x00\x00" * 12000)
            project = {"version": 1, "width": 96, "height": 160, "fps": 4, "caption": {"size": 12},
                       "scenes": [{"text": "First", "duration": 0.5}, {"text": "Second", "audio": "voice.wav"}]}
            (root / "project.json").write_text(json.dumps(project), encoding="utf-8")
            result = render_project(root / "project.json", root / "reel.mp4")
            self.assertAlmostEqual(audio_duration(result), 1.0, delta=0.1)
            probe = subprocess.run([ffmpeg_executable(), "-hide_banner", "-i", str(result)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.assertIn(b"Audio: aac", probe.stderr)


if __name__ == "__main__":
    unittest.main()
