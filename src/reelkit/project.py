"""Project loading and validation. A project never reads outside its directory."""

import copy
import json
import math
from pathlib import Path, PureWindowsPath
import re


def resolve_project_path(root, value, field="path", must_exist=True):
    """Resolve an untrusted, relative asset path without allowing traversal."""
    if not isinstance(value, str) or not value.strip() or "\x00" in value:
        raise ValueError("{} must be a nonempty relative file path".format(field))
    portable = value.replace("\\", "/")
    windows = PureWindowsPath(value)
    if re.match(r"^[A-Za-z][A-Za-z0-9+.-]*:", portable):
        raise ValueError("{} must be a local, relative path; URLs and drive paths are not supported".format(field))
    if Path(portable).is_absolute() or windows.is_absolute() or windows.drive:
        raise ValueError("{} must be relative to the project JSON directory".format(field))
    root = Path(root).resolve()
    resolved = (root / portable).resolve()
    try:
        resolved.relative_to(root)
    except ValueError:
        raise ValueError("{} escapes the project directory: {}".format(field, value))
    if must_exist and not resolved.is_file():
        raise ValueError("{} was not found: {}".format(field, value))
    return resolved


def _number(value, field, low, high, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("{} must be a {}".format(field, "whole number" if integer else "number"))
    if not math.isfinite(value) or not low <= value <= high or (integer and int(value) != value):
        raise ValueError("{} must be {}between {} and {}".format(field, "a whole number " if integer else "", low, high))
    return int(value) if integer else float(value)


def _color(value, field):
    if not isinstance(value, str) or not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
        raise ValueError("{} must be a six-digit hex color, such as #ffffff".format(field))
    return value


def _text(value, field, limit=20000):
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise ValueError("{} must be nonempty text (up to {} characters)".format(field, limit))
    return value.strip()


def load_project(path):
    """Return a normalized dict. Internal keys begin with ``_``; JSON is untouched."""
    path = Path(path).resolve()
    try:
        with path.open("r", encoding="utf-8-sig") as handle:
            project = json.load(handle)
    except (OSError, json.JSONDecodeError) as error:
        raise ValueError("Cannot read project JSON {}: {}".format(path.name, error)) from error
    if not isinstance(project, dict):
        raise ValueError("Project JSON must be an object")
    project = copy.deepcopy(project)
    # Never trust serialized internal keys; all resolved paths are derived here.
    project = {key: value for key, value in project.items() if not key.startswith("_")}
    if type(project.get("version")) is not int or project.get("version") != 1:
        raise ValueError("version must be 1")
    project["title"] = _text(project.get("title", "Untitled reel"), "title", 200)
    for key, default in (("width", 720), ("height", 1280)):
        project[key] = _number(project.get(key, default), key, 16, 4096, integer=True)
        if project[key] % 2:
            raise ValueError("{} must be even for H.264 video".format(key))
    project["fps"] = _number(project.get("fps", 30), "fps", 1, 60, integer=True)
    project["background"] = _color(project.get("background", "#101827"), "background")
    caption = project.setdefault("caption", {})
    if not isinstance(caption, dict):
        raise ValueError("caption must be an object")
    caption = {key: value for key, value in caption.items() if not key.startswith("_")}
    project["caption"] = caption
    caption["size"] = _number(caption.get("size", 52), "caption.size", 8, 240, integer=True)
    caption["position"] = _number(caption.get("position", 0.5), "caption.position", 0.15, 0.85)
    for key, default in (("color", "#ffffff"), ("highlight", "#99f3c4")):
        caption[key] = _color(caption.get(key, default), "caption." + key)
    if "font" in caption:
        caption["_font"] = resolve_project_path(path.parent, caption["font"], "caption.font")
    scenes = project.get("scenes")
    if not isinstance(scenes, list) or not 1 <= len(scenes) <= 500:
        raise ValueError("scenes must contain between 1 and 500 scene objects")
    seen = set()
    for index, scene in enumerate(scenes):
        field = "scenes[{}]".format(index)
        if not isinstance(scene, dict):
            raise ValueError("{} must be an object".format(field))
        scene = {key: value for key, value in scene.items() if not key.startswith("_")}
        scenes[index] = scene
        identifier = scene.setdefault("id", "scene-{}".format(index + 1))
        if not isinstance(identifier, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", identifier):
            raise ValueError("{}.id must use 1–80 letters, digits, hyphens or underscores".format(field))
        if identifier in seen:
            raise ValueError("Duplicate scene id: {}".format(identifier))
        seen.add(identifier)
        scene["text"] = _text(scene.get("text"), field + ".text")
        for key in ("image", "audio"):
            if key in scene:
                scene["_" + key] = resolve_project_path(path.parent, scene[key], field + "." + key)
        if "duration" in scene:
            scene["duration"] = _number(scene["duration"], field + ".duration", 0.05, 3600)
        if "phrases" in scene:
            phrases = scene["phrases"]
            if not isinstance(phrases, list) or not phrases:
                raise ValueError("{}.phrases must be a nonempty list of text chunks".format(field))
            scene["phrases"] = [_text(p, field + ".phrases", 1000) for p in phrases]
            if " ".join(" ".join(scene["phrases"]).split()) != " ".join(scene["text"].split()):
                raise ValueError("{}.phrases must contain the narration text in the same order".format(field))
        if "words" in scene:
            if not isinstance(scene["words"], list) or not scene["words"]:
                raise ValueError("{}.words must be a nonempty list".format(field))
            previous_end = 0.0
            for word_index, word in enumerate(scene["words"]):
                prefix = "{}.words[{}]".format(field, word_index)
                if not isinstance(word, dict):
                    raise ValueError("{} must be an object".format(prefix))
                word["text"] = _text(word.get("text"), prefix + ".text", 200)
                word["start"] = _number(word.get("start"), prefix + ".start", 0, 3600)
                word["end"] = _number(word.get("end"), prefix + ".end", 0, 3600)
                if word["end"] <= word["start"] or word["start"] + 1e-6 < previous_end:
                    raise ValueError("{} timings must be positive, ordered and non-overlapping".format(prefix))
                previous_end = word["end"]
            if "duration" in scene and previous_end > scene["duration"] + 0.05:
                raise ValueError("{}.duration ends before the last word; extend it or correct word timings".format(field))
            if " ".join(w["text"] for w in scene["words"]).split() != scene["text"].split():
                raise ValueError("{}.words text must match the narration text in order".format(field))
    project["_root"] = path.parent
    project["_path"] = path
    return project
