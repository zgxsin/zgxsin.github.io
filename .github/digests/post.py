"""Render the digest and its citations as a Jekyll post."""

from datetime import datetime
from html import escape
import json
import re
from urllib.parse import quote, urlencode
from urllib.request import urlopen


READINESS_LEVELS = (
    "Research prototype", "Pilot-ready", "Deployment-ready for the stated use", "Insufficient evidence",
)


def markdown_text(value):
    text = escape(" ".join(value.split()), quote=False)
    return re.sub(r"([\\`*_\[\]])", r"\\\1", text).replace("{", "&#123;").replace("}", "&#125;")


def render_video(video_id, alt, caption):
    query = urlencode({"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"})
    try:
        with urlopen(f"https://www.youtube.com/oembed?{query}", timeout=8) as response:
            if json.load(response).get("type") != "video":
                return None
    except (OSError, ValueError):
        return None
    caption = markdown_text(caption).replace('"', "&quot;")
    return (
        '{% include video.html youtube="' + video_id + '" '
        f'alt="{alt}" caption="{caption}" %}}'
    )


def render(
    day, entries, updates, *, author, slug, title, category, subject, video_alt,
    include_readiness=True, link_titles=False,
):
    edition_date = datetime.fromisoformat(day)
    display_date = f"{edition_date:%B} {edition_date.day}, {edition_date.year}"
    lines = [
        "---", f'title: "{title} | {display_date}"',
        "published: true", f"date: {day}", f"author: {json.dumps(author, ensure_ascii=False)}",
        f"slug: {slug}", f"categories: [{category}, ai-generated]", "---", "",
    ]
    grouped = {}
    used = set()
    if not isinstance(updates, list) or len(updates) > 6:
        raise ValueError("Invalid digest selection")
    for update in updates:
        index = update["id"]
        if type(index) is not int or not 0 <= index < len(entries) or index in used:
            raise ValueError("Invalid or duplicate digest source index")
        used.add(index)
        if include_readiness and update["readiness"] not in READINESS_LEVELS:
            raise ValueError("Invalid application readiness level")
        section = " ".join(update["section"].split())
        if not section or section.casefold() in {"application readiness", "references"}:
            raise ValueError("Invalid digest section heading")
        grouped.setdefault(section, []).append((entries[index], update))
    if not used:
        lines.extend([f"No new {subject} updates met the criteria in today's source scan.", ""])
        return "\n".join(lines)

    readiness = []
    references = ["## References", "", '{::options footnote_backlink="" /}', ""]
    number = 0
    seen_videos = set()
    for section, items in grouped.items():
        heading = re.sub(r"(?<!&)#", "&#35;", markdown_text(section))
        lines.extend([f"## {heading}", ""])
        for source, update in items:
            number += 1
            title = markdown_text(source["title"])
            url = quote(source["url"], safe=":/?&=%+-._~")
            display_title = f"[{title}](<{url}>)" if link_titles else title
            citation = f"[^ref-{number}]"
            summary = f"{markdown_text(update['summary'])} {markdown_text(update['why_it_matters'])}".strip()
            lines.append(
                f"- **{display_title}** ({source['published']:%b %d}). {summary}{citation}"
            )
            if include_readiness:
                assessment = [
                    f"  - **Readiness** ({update['readiness']}). {markdown_text(update['readiness_evidence'])}",
                    f"  - **Pros.** {markdown_text(update['pros'])}",
                    f"  - **Cons.** {markdown_text(update['cons'])}",
                ]
                if update.get("inline_readiness", False):
                    lines.extend(assessment)
                else:
                    readiness.extend([f"- **{title}**{citation}", *assessment])
            videos = source.get("videos", {})
            for video in update.get("videos", []):
                if not isinstance(video, dict):
                    continue
                video_id, caption = video.get("id"), video.get("caption")
                if not isinstance(video_id, str) or video_id not in videos or video_id in seen_videos:
                    continue
                if not isinstance(caption, str) or not caption.strip():
                    continue
                seen_videos.add(video_id)
                markup = render_video(video_id, video_alt, caption)
                if markup:
                    lines.extend(["", markup, ""])
            references.append(
                f"{citation}: [{title}](<{url}>)"
                f" — {markdown_text(source['source'])}, {source['published']:%Y-%m-%d}."
            )
        lines.append("")
    if readiness:
        lines.extend(["## Application Readiness", "", *readiness, ""])
    lines.extend([*references, ""])
    return "\n".join(lines)
