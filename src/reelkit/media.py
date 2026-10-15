"""Portable FFmpeg helpers; all commands use argument lists and no shell."""

import math
from pathlib import Path
import re
import subprocess
import tempfile
import wave

import imageio_ffmpeg


# Restrict content sniffing as well as path syntax: a local M3U/concat file can
# otherwise cause FFmpeg to fetch remote URLs or open unrelated local files.
_INPUT_RESTRICTIONS = ["-protocol_whitelist", "file,pipe", "-format_whitelist", "wav,mp3,mov,ogg,flac,aiff,aac"]


def ffmpeg_executable():
    return imageio_ffmpeg.get_ffmpeg_exe()


def audio_duration(path):
    """Read duration through the bundled FFmpeg (no separate ffprobe needed)."""
    result = subprocess.run(
        [ffmpeg_executable(), "-hide_banner", "-nostdin"] + _INPUT_RESTRICTIONS + ["-i", str(path)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=False,
    )
    diagnostic = result.stderr.decode("utf-8", errors="replace")
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", diagnostic)
    if not match:
        raise ValueError("Cannot read audio duration for {}. Use a valid WAV, MP3, M4A or OGG file.".format(Path(path).name))
    hours, minutes, seconds = map(float, match.groups())
    duration = hours * 3600 + minutes * 60 + seconds
    if not math.isfinite(duration) or duration <= 0 or duration > 3600:
        raise ValueError("Audio {} must be between 0 and 3600 seconds".format(Path(path).name))
    return duration


def scene_duration(scene):
    word_end = scene.get("words", [{}])[-1].get("end", 0)
    if scene.get("_audio"):
        return max(scene.get("duration", 0), audio_duration(scene["_audio"]), word_end + 0.10)
    if "duration" in scene:
        return scene["duration"]
    # 155 words/minute is a planning estimate, not forced speech stretching.
    return max(1.2, len(scene["text"].split()) / (155 / 60) + 0.30, word_end + 0.10)


def write_audio_track(scenes, durations, destination, sample_rate=24000):
    """Concatenate narration with scene-length silence; never add sound effects."""
    with wave.open(str(destination), "wb") as output:
        output.setnchannels(1)
        output.setsampwidth(2)
        output.setframerate(sample_rate)
        for scene, duration in zip(scenes, durations):
            remaining = int(round(duration * sample_rate)) * 2
            if scene.get("_audio"):
                with tempfile.TemporaryFile() as diagnostic:
                    command = [ffmpeg_executable(), "-v", "error", "-nostdin"] + _INPUT_RESTRICTIONS + ["-i", str(scene["_audio"]),
                               "-t", "{:.8f}".format(duration), "-vn", "-ar", str(sample_rate), "-ac", "1",
                               "-f", "s16le", "pipe:1"]
                    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=diagnostic)
                    try:
                        while True:
                            block = process.stdout.read(65536)
                            if not block:
                                break
                            keep = block[:remaining]
                            output.writeframesraw(keep)
                            remaining -= len(keep)
                        code = process.wait()
                    finally:
                        process.stdout.close()
                        if process.poll() is None:
                            process.kill()
                            process.wait()
                    if code:
                        diagnostic.seek(0)
                        detail = diagnostic.read().decode("utf-8", errors="replace")[-1500:]
                        raise ValueError("Cannot decode narration {}: {}".format(scene["id"], detail))
            silence = b"\x00" * 65536
            while remaining:
                block = silence[:remaining]
                output.writeframesraw(block)
                remaining -= len(block)


def srt_timestamp(seconds):
    milliseconds = int(round(max(0, seconds) * 1000))
    hours, milliseconds = divmod(milliseconds, 3600000)
    minutes, milliseconds = divmod(milliseconds, 60000)
    seconds, milliseconds = divmod(milliseconds, 1000)
    return "{:02d}:{:02d}:{:02d},{:03d}".format(hours, minutes, seconds, milliseconds)
