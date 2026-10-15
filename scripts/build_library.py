"""Build the static reel cards from the public catalog; no packages required."""
import argparse
from hashlib import sha256
from html import escape
import json
import math
from pathlib import Path
import re
from urllib.parse import quote

DOCS = Path(__file__).resolve().parents[1] / "docs"
CATEGORY_ORDER = ["History", "Science", "Programming", "Fiction", "Design"]


def local_file(value, suffixes):
    if not isinstance(value, str) or "\\" in value:
        raise ValueError("Catalog assets need relative forward-slash paths")
    path = DOCS / value
    if Path(value).is_absolute() or ".." in Path(value).parts or not path.resolve().is_relative_to(DOCS.resolve()):
        raise ValueError("Catalog assets must stay inside docs")
    if not path.is_file() or path.suffix.lower() not in suffixes or not path.stat().st_size:
        raise ValueError("Missing or invalid catalog asset: " + value)
    return quote(value, safe="/.-_")


def build():
    reels = json.loads((DOCS / "reels.json").read_text(encoding="utf-8"))
    if not isinstance(reels, list) or not reels:
        raise ValueError("The reel catalog must be a nonempty array")
    cards, ids, categories = [], set(), set()
    for reel in reels:
        identity = reel["id"]
        if not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,79}", identity) or identity in ids:
            raise ValueError("Reel IDs must be unique lowercase slugs")
        ids.add(identity)
        category = reel["category"]
        if category not in CATEGORY_ORDER or reel["language"] != "en":
            raise ValueError("Unknown category or non-English reel")
        categories.add(category)
        duration = reel["duration"]
        if isinstance(duration, bool) or not isinstance(duration, (int, float)) or not math.isfinite(duration) or not 0 < duration < 3600:
            raise ValueError("A reel needs a positive duration under one hour")
        seconds = int(math.ceil(duration))
        stamp = "{}:{:02d}".format(seconds // 60, seconds % 60)
        video = local_file(reel["video"], {".mp4"})
        poster = local_file(reel["poster"], {".jpg", ".png", ".webp"})
        credit = local_file(reel["credits"], {".md"})
        # Content hashes keep a replaced reel fresh for returning visitors.
        video += "?v=" + sha256((DOCS / reel["video"]).read_bytes()).hexdigest()[:10]
        poster += "?v=" + sha256((DOCS / reel["poster"]).read_bytes()).hexdigest()[:10]
        title = escape(reel["title"])
        description = escape(reel["description"])
        credit = "https://github.com/alexkubica/reelkit/blob/main/docs/" + credit
        cards.append('''        <article class="reel-card" id="{id}" data-category="{category}">
          <div class="reel-card-meta"><span class="reel-category">{category}</span><span aria-label="Duration: {seconds} seconds">{stamp}</span></div>
          <video controls playsinline preload="metadata" poster="./{poster}" aria-labelledby="title-{id}">
            <source src="./{video}" type="video/mp4">
            Your browser cannot play this video. <a href="./{video}">Download the MP4.</a>
          </video>
          <h2 id="title-{id}"><a href="#{id}">{title}</a></h2>
          <p class="reel-card-description">{description}</p>
          <p class="reel-card-error" hidden>The video couldn’t load. Try the MP4 download below.</p>
          <div class="reel-card-links"><a href="./{video}" download="{id}.mp4">Download MP4 <span aria-hidden="true">↓</span></a><a href="{credit}">Story &amp; credits <span aria-hidden="true">↗</span></a></div>
        </article>'''.format(id=identity, category=escape(category), seconds=seconds, stamp=stamp,
                             poster=poster, video=video, title=title, description=description, credit=credit))
    buttons = ['          <button type="button" data-category="all" aria-pressed="true">All stories</button>']
    for category in CATEGORY_ORDER:
        if category in categories:
            buttons.append('          <button type="button" data-category="{0}" aria-pressed="false">{0}</button>'.format(category))
    replacements = {"reel-cards": "\n".join(cards), "reel-filters": "\n".join(buttons),
                    "reel-summary": "          {} {} to get lost in".format(len(reels), "story" if len(reels) == 1 else "stories")}
    target = DOCS / "library.html"
    original = target.read_text(encoding="utf-8")
    result = original
    for name, value in replacements.items():
        pattern = r"(<!-- " + name + r":start -->\n).*?(<!-- " + name + r":end -->)"
        result, changes = re.subn(pattern, lambda match: match[1] + value + "\n" + match[2], result, flags=re.S)
        if changes != 1:
            raise ValueError("Missing or duplicated library marker: " + name)
    return target, original, result, len(reels)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if the checked-in page needs regeneration")
    args = parser.parse_args()
    target, original, result, count = build()
    if args.check:
        if original != result:
            raise SystemExit("Library is stale. Run: python scripts/build_library.py")
        print("Library catalog and {} story cards are valid.".format(count))
    else:
        target.write_text(result, encoding="utf-8")
        print("Built {} story cards in docs/library.html".format(count))


if __name__ == "__main__":
    main()
