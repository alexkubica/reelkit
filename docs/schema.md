# Project format: version 1

A ReelKit project is a UTF-8 JSON file. All asset paths are resolved relative to that file, must stay inside its directory, and must refer to local files. Use forward slashes in JSON paths so projects travel cleanly between Windows, macOS, and Linux. URLs and absolute paths are unsupported.

```json
{
  "version": 1,
  "title": "A small idea, clearly explained",
  "width": 720,
  "height": 1280,
  "fps": 30,
  "background": "#101820",
  "caption": {
    "size": 52,
    "color": "#FFFFFF",
    "highlight": "#78E6C5",
    "position": 0.5
  },
  "scenes": [
    {
      "id": "opening",
      "image": "art/opening.png",
      "text": "One idea. A clear visual. A good story.",
      "phrases": ["One idea.", "A clear visual.", "A good story."],
      "duration": 4.0
    }
  ]
}
```

## Project properties

| Property | Meaning |
| --- | --- |
| `version` | Format version; use `1`. |
| `title` | Human-readable project title. It is metadata, not an additional title drawn over subtitles. |
| `width`, `height` | Even integers from `16` to `4096`, in pixels. Defaults: `720 × 1280`. |
| `fps` | Integer output frames per second from `1` to `60`. Default: `30`. |
| `background` | Background color as a six-digit hexadecimal string, for example `#101820`. |
| `caption` | Shared subtitle settings, described below. |
| `scenes` | Ordered array of `1` to `500` scenes. Scenes play in that order. |

These dimensions and editorial settings are project choices, not platform requirements. Use `reelkit validate project.json` to check the renderer's accepted values before a render.

## Caption settings

| Property | Meaning |
| --- | --- |
| `font` | Optional local relative path to a TrueType or OpenType font. ReelKit bundles Noto Sans and Noto Sans Hebrew under the SIL Open Font License for its default rendering. Supply your own font only when needed and when you have the right to use it. |
| `size` | Integer text size from `8` to `240` pixels. Default: `52`. |
| `color` | Subtitle text color in `#RRGGBB` form. |
| `highlight` | Active-word color in `#RRGGBB` form. |
| `position` | Vertical caption center from `0.15` to `0.85` as a fraction of frame height. Default: `0.5`, around the middle. |

Store text in normal logical reading order, including Hebrew and other right-to-left languages. Do not reverse strings in the project file. The renderer handles bidirectional display order; the selected font still needs glyphs for the language.

## Scene properties

| Property | Meaning |
| --- | --- |
| `id` | Unique scene identifier using `1`–`80` ASCII letters, digits, hyphens, or underscores. Defaults to `scene-1`, `scene-2`, and so on. |
| `image` | Optional local illustration path. Without an image, the project background remains visible. |
| `text` | Narration and caption source text in logical reading order. |
| `phrases` | Optional nonempty array of caption groups. Joined with spaces, they must reproduce `text` in order, ignoring whitespace differences. The renderer further splits long groups into chunks of roughly `3`–`4` words for mobile readability. |
| `duration` | Optional scene duration from `0.05` to `3600` seconds. Set this explicitly for predictable silent scenes. |
| `audio` | Optional local narration file path. Supported containers include WAV, MP3, M4A/MOV, OGG, FLAC, AIFF, and AAC. Remote streams and playlists are unsupported. |
| `words` | Optional ordered word timings, described below. |

An audio scene lasts at least as long as its narration, any explicit duration, and its last word timing plus `0.10` seconds. Setting a shorter duration does not trim narration. A silent scene uses its explicit duration when supplied. Otherwise its duration is estimated at `155` words per minute plus `0.30` seconds, with at least `1.2` seconds and enough time for the final timed word. This estimate is a planning fallback, not an estimate of actual speech alignment. Scene durations are rounded up to a whole output frame.

## Word timings

Use seconds relative to the beginning of the containing scene. Each entry has `text`, `start`, and `end`; times must be finite, nonnegative, no greater than `3600`, in order, and non-overlapping, with an end after the start. The word text must reproduce `text` in order, ignoring whitespace differences. When an explicit scene duration is present, the final word must not run beyond it, apart from a `0.05`-second rounding tolerance.

```json
{
  "id": "spoken-opening",
  "text": "One clear idea.",
  "phrases": ["One clear idea."],
  "audio": "audio/opening.mp3",
  "words": [
    {"text": "One", "start": 0.0, "end": 0.3},
    {"text": "clear", "start": 0.3, "end": 0.65},
    {"text": "idea.", "start": 0.65, "end": 1.1}
  ]
}
```

Word timings align the active-word highlight to known speech boundaries. Without them, the renderer estimates word timing from scene duration and word length; this makes the visual effect approximate. Do not describe estimated timing as forced alignment to recorded speech.

## Portability and capabilities

Keep the JSON and all referenced assets together when moving a project. The format contains no provider credentials and no requirement for a specific operating system. Rendering uses local assets; creating illustrations and synthesizing narration depend on tools and services available in the current environment.

Run `reelkit doctor`, then `reelkit validate project.json` when moving a project to another computer. The optional speech extra and network access are needed only for `reelkit narrate`. For exact CLI arguments, run `reelkit --help` and the relevant subcommand's `--help`.
