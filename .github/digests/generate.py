"""Create a dated Jekyll digest from a topic profile and recent news feeds."""

import argparse
from datetime import date, datetime, timezone
import json
import os
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from feeds import clean_url, collect
from gemini import API_KEY_ENV, DEFAULT_MODEL, generate_json
from post import READINESS_LEVELS, render
from review import drafting_prompt, load_lessons, review_issues, save_lessons


DIGEST_DIR = Path(__file__).resolve().parent
PROFILES = DIGEST_DIR / "profiles"


def select_updates(entries, key, model, *, prompt, include_readiness=True, revision=None):
    properties = {
        "id": {"type": "integer"},
        "section": {"type": "string", "description": "The plain-text heading for this story's group."},
        "summary": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "videos": {
            "type": "array",
            "description": "Select only useful demos from the update's supplied videos map.",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string", "description": "The supplied YouTube video ID."},
                    "caption": {
                        "type": "string",
                        "description": (
                            "One short plain-text sentence telling readers what to look for in this video. "
                            "Name the specific mechanism, workflow step, or result the video demonstrates "
                            "using the supplied context. Skip the video if a specific caption is unsupported."
                        ),
                    },
                },
                "required": ["id", "caption"],
            },
        },
    }
    if include_readiness:
        properties.update({
            "readiness": {"type": "string", "enum": list(READINESS_LEVELS)},
            "readiness_evidence": {"type": "string"},
            "pros": {"type": "string"},
            "cons": {"type": "string"},
            "inline_readiness": {
                "type": "boolean",
                "description": "Place the readiness assessment under this story instead of in Application Readiness.",
            },
        })
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
    input_data = sources if revision is None else {"sources": sources, **revision}
    return generate_json(model=model, prompt=prompt, input_data=input_data, schema=schema, key=key)


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        epilog="Set DIGEST_MODEL to switch models and DIGEST_AUTHOR to override the byline.",
    )
    parser.add_argument("profile", choices=sorted(path.parent.name for path in PROFILES.glob("*/profile.json")))
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--sources-only", action="store_true", help="check feeds without using Gemini or writing a post")
    mode.add_argument("--post-path", action="store_true", help="print the edition path without generating the post")
    parser.add_argument("--date", type=date.fromisoformat, help="edition date supplied by the workflow")
    parser.add_argument("--run-at", type=datetime.fromisoformat, help="shared ISO 8601 timestamp with a timezone offset")
    parser.add_argument("--review", action="store_true", help="review and revise the digest before writing the post")
    args = parser.parse_args()
    if args.run_at is not None and args.run_at.utcoffset() is None:
        parser.error("--run-at requires a timezone offset")
    profile_dir = PROFILES / args.profile
    profile = json.loads((profile_dir / "profile.json").read_text(encoding="utf-8"))
    slug = profile["slug"]
    now = datetime.now(timezone.utc)
    run_time = (args.run_at or now).astimezone(ZoneInfo("Europe/Zurich"))
    day = (args.date or run_time.date()).isoformat()
    posts = Path("_posts")
    path = posts / f"{day}-{slug}.md"
    if not path.exists():
        timestamped_posts = sorted(posts.glob(f"{day}-[0-9][0-9][0-9][0-9]-{slug}.md"))
        path = timestamped_posts[0] if timestamped_posts else posts / f"{day}-{run_time:%H%M}-{slug}.md"
    if args.post_path:
        print(path)
        return
    if path.exists() and not args.sources_only:
        return
    seen = {
        clean_url(url) for post in posts.glob(f"*-{slug}.md")
        for url in re.findall(r"https?://[^\s<>)]+", post.read_text())
    }
    topic = re.compile("|".join(profile["patterns"]), re.I)
    entries = collect(now, seen, sources=profile["sources"], topic=topic)
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
    prompt = (profile_dir / "prompt.md").read_text(encoding="utf-8").strip()
    include_readiness = profile.get("include_readiness", True)
    if include_readiness:
        layout = (DIGEST_DIR / "layout-prompt.md").read_text(encoding="utf-8").strip()
        prompt = f"{prompt}\n\n{layout}"
    lessons_path = profile_dir / "learned-rules.json"
    learned = load_lessons(lessons_path)
    post_options = {field: profile[field] for field in ("slug", "title", "category", "subject", "video_alt")}
    post_options.update(run_time=run_time, include_readiness=include_readiness, link_titles=profile.get("link_titles", False))
    post_options["search_links"] = profile.get("search_links")
    updates = select_updates(
        entries, key, model, prompt=drafting_prompt(prompt, learned), include_readiness=include_readiness,
    ) if entries else []
    content = render(day, entries, updates, author=author, **post_options)
    if args.review:
        review_prompt = (DIGEST_DIR / "review-prompt.md").read_text(encoding="utf-8").strip()
        issues = review_issues(
            content, [entries[update["id"]] for update in updates], prompt=review_prompt, model=model, key=key,
        )
        if issues:
            details = [issue["detail"] for issue in issues]
            print("AI review requested revisions.", *details, sep="\n- ")
            learned = save_lessons(lessons_path, learned, issues)
            revision_prompt = (DIGEST_DIR / "revision-prompt.md").read_text(encoding="utf-8").strip()
            updates = select_updates(
                entries, key, model, prompt=f"{drafting_prompt(prompt, learned)}\n\n{revision_prompt}",
                include_readiness=include_readiness,
                revision={"draft": content, "previous_selection": updates, "review_issues": details},
            )
            content = render(day, entries, updates, author=author, **post_options)
            remaining = review_issues(
                content, [entries[update["id"]] for update in updates],
                prompt=review_prompt, model=model, key=key,
            )
            if remaining:
                save_lessons(lessons_path, learned, remaining)
                details = "\n- ".join(issue["detail"] for issue in remaining)
                raise SystemExit(f"AI review rejected the revised digest.\n- {details}")
        print("AI review approved the digest.")
    with path.open("x", encoding="utf-8") as post:
        post.write(content)


if __name__ == "__main__":
    main()
