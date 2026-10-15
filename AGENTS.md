# Working in ReelKit

ReelKit turns a local JSON project, illustrations, and optional narration into a vertical video. Keep the renderer portable across Windows, macOS, Linux, and suitable cloud runtimes. The repository includes the reusable [create-reel skill](.agents/skills/create-reel/SKILL.md) for video authoring.

## Making videos

Read the skill when creating or revising a reel. Preserve the user's explicit style, length, language, and asset choices. Its editorial defaults are adjustable preferences, not platform requirements.

Run `reelkit doctor` before choosing a production path. Rendering local assets must remain possible without an image-generation service or a speech provider. Use available tools, user-supplied assets, or explain a missing capability when it is essential to the requested result. Do not assume a cloud runtime has desktop applications, a GPU, network access, or the same tools as another computer.

Store work projects and rendered files outside tracked source, or in an ignored directory. Keep sample projects original and safe to redistribute. A request to create a video authorizes the necessary local authoring work; publishing the video to an external destination requires a user request covering that destination.

## Changing the code

- Use Python 3.9-compatible syntax and APIs. Avoid platform-specific shell commands and hard-coded paths.
- Keep project asset paths local, relative to the project JSON, and contained in its directory. Reject URLs and traversal rather than downloading files during a render.
- Invoke external programs with argument lists. Never interpolate project text into a shell command.
- Keep optional network speech synthesis separate from validation and rendering. Fail with a useful capability error when an optional dependency is missing.
- Preserve readable, centered subtitles and correct bidirectional text. Narration text and timing data must stay in logical reading order; apply display reordering only when drawing text.
- Add focused tests for changed timing, path validation, subtitle layout, or render behavior. Run `python -m pytest` for relevant changes. A documentation-only edit does not need an expensive render.
- For a renderer change, also render a short offline example and inspect representative frames. For an audio change, listen to the result when playback is available; report any unverified part honestly.

## Public repository boundary

Do not commit keys, `.env` files, private URLs, account information, transcripts, personal paths, user recordings, or generated runtime outputs. Review staged files and asset licenses before a public push. Keep attribution with any redistributable asset; use synthetic examples instead of copying a user's project into fixtures.

See [CONTRIBUTING.md](CONTRIBUTING.md), [SECURITY.md](SECURITY.md), and the [project schema](docs/schema.md).
