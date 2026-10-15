"""Render vertical reels with Pillow and bundled FFmpeg on all desktop OSes."""

import math
from pathlib import Path
import subprocess
import tempfile

from PIL import Image, ImageOps

from .captions import CaptionPainter, build_caption_cues
from .media import ffmpeg_executable, scene_duration, srt_timestamp, write_audio_track
from .project import load_project


def _artwork(scene, width, height, background):
    if not scene.get("_image"):
        return Image.new("RGB", (width, height), background)
    try:
        with Image.open(scene["_image"]) as source:
            source = ImageOps.exif_transpose(source)
            # Composite transparent artwork on the chosen background.
            if source.mode == "RGBA" or "transparency" in source.info:
                layer = source.convert("RGBA")
                merged = Image.new("RGBA", layer.size, background)
                merged.alpha_composite(layer)
                source = merged
            return ImageOps.fit(source.convert("RGB"), (width, height), method=Image.Resampling.LANCZOS)
    except (OSError, ValueError, Image.DecompressionBombError) as error:
        raise ValueError("Cannot open image for {}: {}".format(scene["id"], error)) from error


def _camera(image, progress, direction):
    # A continuous 0–2.5% push and tiny drift. No bounce or animated transition.
    smooth = progress * progress * (3 - 2 * progress)
    zoom = 1 + 0.025 * smooth
    crop_width, crop_height = image.width / zoom, image.height / zoom
    margin_x = (image.width - crop_width) / 2
    margin_y = (image.height - crop_height) / 2
    center_x = image.width / 2 + direction * margin_x * 0.35
    center_y = image.height / 2 - margin_y * 0.20
    return image.resize(image.size, Image.Resampling.BICUBIC,
                        box=(center_x - crop_width / 2, center_y - crop_height / 2,
                             center_x + crop_width / 2, center_y + crop_height / 2))


def render_project(path, output, draft=False):
    """Render MP4 and a sibling UTF-8 SRT. Return the completed MP4 Path.

    ``draft`` caps the long edge at 640px and the frame rate at 15. Audio stays
    synchronized; output files are atomically replaced after encoding succeeds.
    """
    project = load_project(path)
    output = Path(output).resolve()
    if output.suffix.lower() != ".mp4":
        raise ValueError("Output must have an .mp4 extension")
    protected = {project["_path"], project["caption"].get("_font")}
    protected.update(scene.get("_image") for scene in project["scenes"])
    protected.update(scene.get("_audio") for scene in project["scenes"])
    if output in protected or output.with_suffix(".srt") in protected:
        raise ValueError("Output cannot overwrite the project JSON or a source asset")
    output.parent.mkdir(parents=True, exist_ok=True)
    scale = min(1.0, 640 / max(project["width"], project["height"])) if draft else 1.0
    width = max(16, int(project["width"] * scale) // 2 * 2)
    height = max(16, int(project["height"] * scale) // 2 * 2)
    fps = min(project["fps"], 15) if draft else project["fps"]
    frames = [max(1, math.ceil(scene_duration(scene) * fps)) for scene in project["scenes"]]
    durations = [count / fps for count in frames]
    all_cues = [build_caption_cues(scene, duration) for scene, duration in zip(project["scenes"], durations)]
    srt_lines = []
    offset = 0.0
    cue_number = 1
    for cues, duration in zip(all_cues, durations):
        for cue in cues:
            srt_lines.extend([str(cue_number), "{} --> {}".format(srt_timestamp(offset + cue.start), srt_timestamp(offset + cue.end)), cue.text, ""])
            cue_number += 1
        offset += duration
    with tempfile.TemporaryDirectory(prefix="reelkit-", dir=str(output.parent)) as temporary:
        temporary = Path(temporary)
        encoded = temporary / "render.mp4"
        audio = None
        if any(scene.get("_audio") for scene in project["scenes"]):
            audio = temporary / "narration.wav"
            write_audio_track(project["scenes"], durations, audio)
        command = [ffmpeg_executable(), "-hide_banner", "-loglevel", "error", "-y",
                   "-f", "rawvideo", "-vcodec", "rawvideo", "-pix_fmt", "rgb24",
                   "-s", "{}x{}".format(width, height), "-r", str(fps), "-i", "pipe:0"]
        if audio:
            command.extend(["-i", str(audio), "-map", "0:v:0", "-map", "1:a:0", "-c:a", "aac", "-b:a", "128k"])
        command.extend(["-c:v", "libx264", "-preset", "ultrafast" if draft else "medium", "-crf", "25" if draft else "20",
                        "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(encoded)])
        with tempfile.TemporaryFile() as diagnostic:
            process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=diagnostic)
            try:
                for index, (scene, count, duration, cues) in enumerate(zip(project["scenes"], frames, durations, all_cues)):
                    image = _artwork(scene, width, height, project["background"])
                    painter = CaptionPainter(project["caption"], width, height, scale)
                    cue_index = 0
                    for frame_number in range(count):
                        time = frame_number / fps
                        frame = _camera(image, frame_number / max(1, count - 1), 1 if index % 2 else -1)
                        while cue_index < len(cues) and time >= cues[cue_index].end:
                            cue_index += 1
                        if cue_index < len(cues) and cues[cue_index].start <= time < cues[cue_index].end:
                            painter.paint(frame, cues[cue_index], time)
                        process.stdin.write(frame.tobytes())
                process.stdin.close()
                code = process.wait()
                if code:
                    diagnostic.seek(0)
                    raise ValueError("FFmpeg could not encode this reel: " + diagnostic.read().decode("utf-8", errors="replace")[-2000:])
            except BrokenPipeError as error:
                diagnostic.seek(0)
                detail = diagnostic.read().decode("utf-8", errors="replace")[-2000:]
                raise ValueError("FFmpeg stopped while rendering: " + detail) from error
            finally:
                if process.stdin and not process.stdin.closed:
                    try:
                        process.stdin.close()
                    except BrokenPipeError:
                        pass
                if process.poll() is None:
                    process.kill()
                    process.wait()
        subtitles = temporary / "render.srt"
        subtitles.write_text("\n".join(srt_lines), encoding="utf-8")
        encoded.replace(output)
        subtitles.replace(output.with_suffix(".srt"))
    return output
