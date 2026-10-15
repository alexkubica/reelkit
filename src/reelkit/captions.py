"""Short, stationary captions with word highlighting and bidirectional text."""

from dataclasses import dataclass
from itertools import groupby
from pathlib import Path
import unicodedata

from bidi.algorithm import (
    apply_mirroring, explicit_embed_and_overrides, get_base_level,
    get_embedding_levels, get_empty_storage, reorder_resolved_levels,
    resolve_implicit_levels, resolve_neutral_types, resolve_weak_types,
)
from PIL import Image, ImageDraw, ImageFont, features


@dataclass(frozen=True)
class Word:
    text: str
    start: float
    end: float


@dataclass(frozen=True)
class Cue:
    words: tuple
    start: float
    end: float

    @property
    def text(self):
        return " ".join(word.text for word in self.words)


def _chunks(tokens):
    result = []
    while tokens:
        count = len(tokens) if len(tokens) <= 4 else 3
        result.append(tokens[:count])
        tokens = tokens[count:]
    return result


def build_caption_cues(scene, duration):
    """Use real boundaries when supplied, otherwise estimate only caption timing."""
    tokens = scene["text"].split()
    if scene.get("words"):
        words = [Word(word["text"], word["start"], word["end"]) for word in scene["words"]]
    else:
        start = min(0.08, duration * 0.05)
        span = max(duration - start * 2, duration * 0.5)
        weights = [max(2, min(len(token), 10)) for token in tokens]
        total = sum(weights)
        words = []
        elapsed = 0
        for token, weight in zip(tokens, weights):
            end = elapsed + weight
            words.append(Word(token, start + span * elapsed / total, start + span * end / total))
            elapsed = end
    if scene.get("phrases"):
        sizes = [len(part) for phrase in scene["phrases"] for part in _chunks(phrase.split())]
    else:
        sizes = [len(part) for part in _chunks(tokens)]
    cues = []
    cursor = 0
    for size in sizes:
        selected = tuple(words[cursor:cursor + size])
        cursor += size
        if selected:
            cues.append(Cue(selected, selected[0].start, min(duration, selected[-1].end + 0.08)))
    # Avoid overlapping caption chunks even when speech pauses are very short.
    return [Cue(c.words, c.start, min(c.end, cues[i + 1].start) if i + 1 < len(cues) else c.end)
            for i, c in enumerate(cues)]


def visual_word_runs(tokens):
    """Return (original word index, visual characters, logical characters, RTL).

    Attach word identities before the Unicode bidi algorithm reorders characters.
    This preserves Latin acronyms/numbers embedded in Hebrew while highlighting
    the correct word. Public python-bidi algorithm helpers also work without RAQM.
    """
    text = " ".join(tokens)
    storage = get_empty_storage()
    storage["base_level"] = get_base_level(text)
    storage["base_dir"] = ("L", "R")[storage["base_level"]]
    get_embedding_levels(text, storage, False, False)
    identities = []
    for index, token in enumerate(tokens):
        identities.extend([index] * len(token))
        if index + 1 < len(tokens):
            identities.append(None)
    for index, (char, identity) in enumerate(zip(storage["chars"], identities)):
        char["word_index"] = identity
        char["logical_index"] = index
        # python-bidi 0.6's Python algorithm predates isolate controls. Convert
        # these invisible controls to boundary neutrals rather than asserting.
        if char["type"] in ("LRI", "RLI", "FSI", "PDI"):
            char["type"] = "BN"
    explicit_embed_and_overrides(storage, False)
    resolve_weak_types(storage, False)
    resolve_neutral_types(storage, False)
    resolve_implicit_levels(storage, False)
    reorder_resolved_levels(storage, False)
    apply_mirroring(storage, False)
    runs = []
    for (identity, level), group in groupby(storage["chars"], lambda char: (char["word_index"], char["level"] % 2)):
        chars = list(group)
        if identity is None:
            continue
        visual = "".join(char["ch"] for char in chars)
        logical = "".join(text[char["logical_index"]] for char in sorted(chars, key=lambda char: char["logical_index"]))
        # Strip format controls, which must not consume a visible caption slot.
        visual = "".join(c for c in visual if unicodedata.category(c) != "Cf")
        logical = "".join(c for c in logical if unicodedata.category(c) != "Cf")
        if visual:
            runs.append((identity, visual, logical, bool(level)))
    return runs


def default_font_path():
    font = Path(__file__).parent / "assets" / "fonts" / "NotoSansHebrew-Bold.ttf"
    if not font.is_file():
        raise ValueError("Bundled caption font is missing. Reinstall ReelKit, or set caption.font to a project-relative .ttf file.")
    return font


class CaptionPainter:
    """Cache a caption's fixed geometry; only its active word changes color."""

    def __init__(self, config, width, height, scale=1.0):
        self.config = config
        self.width, self.height = width, height
        self.size = max(8, int(round(config["size"] * scale)))
        self.font_path = config.get("_font") or default_font_path()
        self.latin_path = self.font_path if config.get("_font") else Path(__file__).parent / "assets" / "fonts" / "NotoSans-Bold.ttf"
        if not self.latin_path.is_file():
            self.latin_path = self.font_path
        self.raqm = features.check("raqm")
        self.cache = {}
        self.current_cue = None

    def _font(self, size, latin=False):
        engine = ImageFont.Layout.RAQM if self.raqm else ImageFont.Layout.BASIC
        path = self.latin_path if latin else self.font_path
        try:
            return ImageFont.truetype(str(path), size, layout_engine=engine)
        except OSError as error:
            raise ValueError("Cannot load caption font {}. Supply a valid TTF/OTF file in caption.font.".format(Path(self.font_path).name)) from error

    def _run(self, run):
        if self.raqm:
            return run[2], {"direction": "rtl" if run[3] else "ltr", "language": "he" if run[3] else "en"}
        return run[1], {}

    def _layout(self, cue):
        tokens = [word.text for word in cue.words]
        size = self.size
        probe = ImageDraw.Draw(Image.new("RGBA", (1, 1)))
        while True:
            font = self._font(size)
            latin_font = self._font(size, latin=True)
            def measure(indices):
                runs = visual_word_runs([tokens[i] for i in indices])
                measured = []
                previous = None
                total = 0
                for run in runs:
                    label, options = self._run(run)
                    run_font = font if any("\u0590" <= char <= "\u05ff" for char in run[2]) else latin_font
                    length = probe.textlength(label, font=run_font, **options)
                    spacing = gap if previous is not None and previous != run[0] else 0
                    measured.append((indices[run[0]], label, options, length, spacing, run_font))
                    total += length + spacing
                    previous = run[0]
                return total, measured
            logical_lines = [list(range(len(tokens)))]
            gap = probe.textlength(" ", font=font)
            whole_width = measure(logical_lines[0])[0]
            if whole_width > self.width * 0.86 and len(tokens) > 1:
                middle = (len(tokens) + 1) // 2
                logical_lines = [list(range(middle)), list(range(middle, len(tokens)))]
            lines = []
            max_width = 0
            for indices in logical_lines:
                line_width, measured = measure(indices)
                max_width = max(max_width, line_width)
                lines.append((line_width, measured))
            if max_width <= self.width * 0.88 or size <= 8:
                break
            size -= 2
        stroke = max(1, round(size * 0.075))
        ascent = max(font.getmetrics()[0], latin_font.getmetrics()[0])
        descent = max(font.getmetrics()[1], latin_font.getmetrics()[1])
        line_height = ascent + descent + max(2, round(size * 0.10))
        pad = stroke * 3 + 4
        stamp_width = min(self.width, int(max_width + 2 * pad + 2))
        stamp_height = len(lines) * line_height + 2 * pad
        positions = []
        for line_index, (line_width, measured) in enumerate(lines):
            x = (stamp_width - line_width) / 2
            y = pad + ascent + line_index * line_height
            for word_index, label, options, length, spacing, run_font in measured:
                x += spacing
                positions.append((word_index, (x, y), label, options, run_font))
                x += length
        return font, stroke, (stamp_width, stamp_height), positions

    def _stamp(self, cue, active):
        key = (cue, active)
        if key in self.cache:
            return self.cache[key]
        layout_key = (cue, "layout")
        if layout_key not in self.cache:
            self.cache[layout_key] = self._layout(cue)
        font, stroke, dimensions, positions = self.cache[layout_key]
        stamp = Image.new("RGBA", dimensions, (0, 0, 0, 0))
        draw = ImageDraw.Draw(stamp)
        for word_index, position, label, options, run_font in positions:
            fill = self.config["highlight"] if word_index == active else self.config["color"]
            draw.text((position[0] + 1, position[1] + 2), label, font=run_font, anchor="ls", fill="#000000",
                      stroke_width=stroke + 1, stroke_fill="#000000", **options)
            draw.text(position, label, font=run_font, anchor="ls", fill=fill,
                      stroke_width=stroke, stroke_fill="#111827", **options)
        self.cache[key] = stamp
        return stamp

    def paint(self, frame, cue, time):
        if cue != self.current_cue:
            self.cache.clear()
            self.current_cue = cue
        active = 0
        for index, word in enumerate(cue.words):
            if time >= word.start:
                active = index
        stamp = self._stamp(cue, active)
        x = (self.width - stamp.width) // 2
        y = int(self.height * self.config["position"] - stamp.height / 2)
        frame.paste(stamp, (x, y), stamp)
