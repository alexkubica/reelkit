"""Optional online speech adapter. No credentials or provider SDK are bundled."""
import asyncio
import html
import json
import math
from pathlib import Path
import re
import shutil
import tempfile
import unicodedata

from .media import audio_duration
from .project import load_project, resolve_project_path


def align_words(text, events, duration):
    """Preserve displayed spelling/punctuation; identify approximate alignment."""
    tokens = text.split()
    if not tokens or isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or duration <= 0:
        raise ValueError("Caption alignment needs nonempty text and a positive audio duration")
    def normalized(value):
        return "".join(char for char in html.unescape(value).casefold() if unicodedata.category(char)[0] in ("L", "N"))
    if len(tokens) == len(events) and events:
        words = []
        for index, (token, event) in enumerate(zip(tokens, events)):
            if not isinstance(event, dict) or not isinstance(event.get("text"), str) or normalized(token) != normalized(event["text"]):
                break
            offset, length = event.get("offset"), event.get("duration")
            if any(isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) for value in (offset, length)):
                break
            start = offset / 10_000_000
            end = (offset + length) / 10_000_000
            if start < 0 or length <= 0 or end > duration + 0.05:
                break
            if index + 1 < len(events):
                following = events[index + 1]
                following_offset = following.get("offset") if isinstance(following, dict) else None
                if isinstance(following_offset, bool) or not isinstance(following_offset, (int, float)) or not math.isfinite(following_offset):
                    break
                end = min(end, following_offset / 10_000_000)
            end = min(end, duration)
            if round(end, 6) <= round(start, 6) or (words and start < words[-1]["end"]):
                break
            words.append({"text": token, "start": round(start, 6), "end": round(end, 6)})
        if len(words) == len(tokens):
            return words, "word-boundaries"
    # Providers may split Latin initials or numbers differently. Be explicit
    # instead of fabricating precise alignment or dropping caption words.
    total = sum(max(1, len(token)) for token in tokens)
    start, result = 0.0, []
    for token in tokens:
        end = start + duration * max(1, len(token)) / total
        result.append({"text": token, "start": round(start, 6), "end": round(end, 6)})
        start = end
    return result, "estimated"


def narrate_project(path, voice="he-IL-AvriNeural", rate="+15%", force=False):
    if not re.fullmatch(r"[A-Za-z0-9:._-]{1,120}", voice):
        raise ValueError("Use a valid provider voice ID, such as he-IL-AvriNeural")
    if not re.fullmatch(r"[+-]\d{1,3}%", rate):
        raise ValueError("rate must look like +15% or -5%")
    try:
        import edge_tts
    except ImportError as error:
        raise ValueError('Online narration is optional. Install it with: python -m pip install -e ".[voice]"') from error
    project = load_project(path)
    root, project_path = project["_root"], project["_path"]
    data = json.loads(project_path.read_text(encoding="utf-8-sig"))
    destinations = []
    for scene in project["scenes"]:
        value = "build/voice/{}.mp3".format(scene["id"])
        target = resolve_project_path(root, value, "generated narration", must_exist=False)
        if not force and (scene.get("audio") or target.exists()):
            raise ValueError("{} already has narration. Use --force to replace generated references; original supplied files stay intact.".format(scene["id"]))
        destinations.append((value, target))
    staging_root = resolve_project_path(root, "build", "narration build directory", must_exist=False)
    staging_root.mkdir(parents=True, exist_ok=True)

    async def generate(temporary):
        updates = []
        for scene in project["scenes"]:
            output = temporary / (scene["id"] + ".mp3")
            events = []
            try:
                communicate = edge_tts.Communicate(scene["text"], voice, rate=rate, boundary="WordBoundary")
                with output.open("wb") as handle:
                    async for chunk in communicate.stream():
                        if chunk["type"] == "audio":
                            handle.write(chunk["data"])
                        elif chunk["type"] == "WordBoundary":
                            events.append(chunk)
            except Exception as error:
                raise RuntimeError("Speech generation failed for {}. Check network/service availability; the project JSON was not changed. {}".format(scene["id"], type(error).__name__)) from error
            length = audio_duration(output)
            words, alignment = align_words(scene["text"], events, length)
            updates.append((output, words, alignment, max(length + 0.12, words[-1]["end"] + 0.12)))
        return updates

    with tempfile.TemporaryDirectory(prefix="narrate-", dir=str(staging_root)) as temporary:
        updates = asyncio.run(generate(Path(temporary)))
        # Check every destination again before committing the generated files.
        for relative, _ in destinations:
            resolve_project_path(root, relative, "generated narration", must_exist=False)
        for scene, destination, update in zip(data["scenes"], destinations, updates):
            relative, target = destination
            audio, words, alignment, length = update
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(audio, target)
            scene.update(audio=relative, words=words, alignment=alignment, duration=max(scene.get("duration", 0), length))
        # Validate the resulting public-format JSON before replacing the source.
        staged_json = root / ("." + project_path.name + ".narrate.tmp")
        try:
            staged_json.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            load_project(staged_json)
            staged_json.replace(project_path)
        finally:
            if staged_json.exists():
                staged_json.unlink()
    return project_path
