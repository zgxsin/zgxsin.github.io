"""Create a dated Jekyll digest from recent robotics news feeds."""

import argparse
from datetime import date, datetime, timezone
import os
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from feeds import clean_url, collect
from gemini import API_KEY_ENV, DEFAULT_MODEL, generate_json
from post import READINESS_LEVELS, SECTIONS, render


SLUG = "robotics-hardware-and-sensors-digest"


def select_updates(entries, key, model):
    properties = {
        "id": {"type": "integer"},
        "section": {"type": "string", "enum": list(SECTIONS)},
        "summary": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "readiness": {"type": "string", "enum": list(READINESS_LEVELS)},
        "readiness_evidence": {"type": "string"},
        "pros": {"type": "string"},
        "cons": {"type": "string"},
        "video_ids": {"type": "array", "items": {"type": "string"}},
    }
    sources = [
        {
            "id": index,
            **{field: entry[field] for field in ("title", "summary", "source", "published")},
            "videos": entry.get("videos", {}),
        }
        for index, entry in enumerate(entries)
    ]
    schema = {
        "type": "array", "maxItems": 6,
        "items": {"type": "object", "properties": properties, "required": list(properties)},
    }
    prompt = Path(__file__).with_name("prompt.md").read_text(encoding="utf-8").strip()
    return generate_json(model=model, prompt=prompt, input_data=sources, schema=schema, key=key)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Set DIGEST_MODEL to switch models and DIGEST_AUTHOR to override the byline.",
    )
    parser.add_argument("--sources-only", action="store_true", help="check feeds without using Gemini or writing a post")
    parser.add_argument("--date", type=date.fromisoformat, help="edition date supplied by the workflow")
    args = parser.parse_args()
    now = datetime.now(timezone.utc)
    day = (args.date or now.astimezone(ZoneInfo("Europe/Zurich")).date()).isoformat()
    posts = Path("_posts")
    path = posts / f"{day}-{SLUG}.md"
    if path.exists() and not args.sources_only:
        return
    seen = {
        clean_url(url) for post in posts.glob(f"*-{SLUG}.md")
        for url in re.findall(r"https?://[^\s<>)]+", post.read_text())
    }
    entries = collect(now, seen)
    print(f"Found {len(entries)} recent candidate updates.")
    if args.sources_only:
        for entry in entries:
            print(f"{entry['source']}: {entry['url']}")
        return
    key = os.environ.get(API_KEY_ENV)
    if not key:
        raise SystemExit(f"Set {API_KEY_ENV} before running the digest.")
    model = os.environ.get("DIGEST_MODEL") or DEFAULT_MODEL
    author = os.environ.get("DIGEST_AUTHOR") or model.replace("-", " ").title()
    updates = select_updates(entries, key, model) if entries else []
    content = render(day, entries, updates, author=author)
    with path.open("x", encoding="utf-8") as post:
        post.write(content)


if __name__ == "__main__":
    main()
