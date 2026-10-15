"""Small cross-platform command line. Rendering never makes network requests."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys

from PIL import features

from . import __version__
from .media import ffmpeg_executable
from .project import load_project
from .render import render_project


def initialize(directory, language="en"):
    destination = Path(directory).resolve()
    if destination.exists() and (not destination.is_dir() or any(destination.iterdir())):
        raise ValueError("Choose a new or empty directory; init never overwrites a project")
    source = Path(__file__).parent / "assets" / "demo"
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source / "images", destination / "images")
    shutil.copyfile(source / (language + ".json"), destination / "project.json")
    shutil.copyfile(source / "ASSETS.md", destination / "ASSETS.md")
    return destination / "project.json"


def doctor():
    print("ReelKit {} | Python {} | {}".format(__version__, sys.version.split()[0], sys.platform))
    executable = ffmpeg_executable()
    result = subprocess.run([executable, "-version"], capture_output=True, text=True, check=True)
    print(result.stdout.splitlines()[0])
    print("Text shaping: {}".format("RAQM" if features.check("raqm") else "python-bidi fallback (Hebrew + Latin)"))
    fonts = Path(__file__).parent / "assets" / "fonts"
    for name in ("NotoSansHebrew-Bold.ttf", "NotoSans-Bold.ttf"):
        if not (fonts / name).is_file():
            raise ValueError("Bundled font missing: {}. Reinstall ReelKit.".format(name))
    print("Fonts: bundled Noto Sans / Noto Sans Hebrew")
    try:
        import edge_tts  # noqa: F401
        print("Optional online narration: installed; use narrate explicitly to send text")
    except ImportError:
        print("Optional online narration: not installed; supplied audio and silent renders work")
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(prog="reelkit", description="Create illustrated reels with stable, centered captions.")
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("doctor", help="Check local FFmpeg, fonts, text shaping and optional voice tools")
    init = commands.add_parser("init", help="Copy a self-contained offline example into a new directory")
    init.add_argument("directory")
    init.add_argument("--language", choices=("en", "he"), default="en")
    validate = commands.add_parser("validate", help="Validate project JSON and local input paths")
    validate.add_argument("project")
    render = commands.add_parser("render", help="Render MP4 + SRT locally; no network")
    render.add_argument("project")
    render.add_argument("--output", "-o")
    render.add_argument("--draft", action="store_true", help="Cap the long edge at 640 pixels and frame rate at 15")
    narration = commands.add_parser("narrate", help="Send scene text to Microsoft's online speech service (optional)")
    narration.add_argument("project")
    narration.add_argument("--voice", default="he-IL-AvriNeural")
    narration.add_argument("--rate", default="+15%")
    narration.add_argument("--force", action="store_true", help="Replace generated narration references and timing in the project")
    args = parser.parse_args(argv)
    try:
        if args.command == "doctor":
            return doctor()
        if args.command == "init":
            path = initialize(args.directory, args.language)
            print("Created {}".format(path))
            print('Next: reelkit render "{}" --draft'.format(path))
        elif args.command == "validate":
            project = load_project(args.project)
            print("Valid project: {} ({} scenes)".format(project["title"], len(project["scenes"])))
        elif args.command == "render":
            path = Path(args.project).resolve()
            output = args.output or str(path.parent / "build" / "reel.mp4")
            print("Rendering locally; a full-resolution reel can take a few minutes.", flush=True)
            rendered = render_project(path, output, draft=args.draft)
            print("Video: {}\nCaptions: {}".format(rendered, rendered.with_suffix(".srt")))
        elif args.command == "narrate":
            from .voice import narrate_project
            print("Online narration sends this project's scene text to Microsoft's speech service.", flush=True)
            output = narrate_project(args.project, args.voice, args.rate, force=args.force)
            print("Narration and word timings saved; render {}".format(output))
        return 0
    except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as error:
        print("reelkit: {}".format(error), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
