"""Read and filter digest news feeds."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
import json
import re
import sys
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree


ATOM = "{http://www.w3.org/2005/Atom}"
RSS_CONTENT = "{http://purl.org/rss/1.0/modules/content/}"
YOUTUBE_LINK = re.compile(
    r"https://(?:(?:www\.)?youtu\.be/|(?:www\.)?youtube\.com/(?:watch\?v=|embed/)|"
    r"(?:www\.)?youtube-nocookie\.com/embed/)([A-Za-z0-9_-]{11})(?![A-Za-z0-9_-])",
    re.I,
)


def plain_text(value):
    return " ".join(unescape(re.sub(r"<[^>]+>", " ", value or "")).split())


def clean_url(value):
    parts = urlsplit(value.strip())
    if parts.scheme not in ("http", "https") or not parts.hostname or parts.username:
        return ""
    query = [(key, val) for key, val in parse_qsl(parts.query) if not key.startswith("utm_")]
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip("/"), urlencode(query), ""))


def source_videos(markup):
    videos = {}
    markup = unescape(markup)
    for match in YOUTUBE_LINK.finditer(markup):
        context = markup[max(0, match.start() - 360):match.end() + 450]
        videos.setdefault(match[1], plain_text(context)[:350])
    return videos


def read_feed(name, config, topic):
    url = config if isinstance(config, str) else config["url"]
    request = Request(url, headers={"User-Agent": "NewsDigest/1.0"})
    with urlopen(request, timeout=20) as response:
        data = response.read(4_000_000)
    feed_format = "xml" if isinstance(config, str) else config.get("format", "xml")
    if feed_format != "xml":
        return read_json_entries(name, json.loads(data), topic, feed_format)
    root = ElementTree.fromstring(data)
    if root.tag not in ("rss", ATOM + "feed"):
        raise ValueError("unsupported feed format")

    entries = []
    for item in root.findall("./channel/item") + root.findall(f"{ATOM}entry"):
        title = plain_text(item.findtext("title") or item.findtext(f"{ATOM}title"))
        description = item.findtext("description") or item.findtext(f"{ATOM}summary") or ""
        content = item.findtext(f"{RSS_CONTENT}encoded") or item.findtext(f"{ATOM}content") or ""
        summary = plain_text(description or content)
        link = item.findtext("link") or next(
            (node.get("href", "") for node in item.findall(f"{ATOM}link") if node.get("rel", "alternate") == "alternate"),
            "",
        )
        date = item.findtext("pubDate")
        try:
            published = (
                parsedate_to_datetime(date) if date else datetime.fromisoformat(
                    item.findtext(f"{ATOM}published") or item.findtext(f"{ATOM}updated") or ""
                )
            )
            link = clean_url(link)
        except ValueError:
            continue
        if title and link and published.tzinfo and topic.search(title + " " + summary):
            entries.append({
                "title": title, "summary": summary[:1800], "url": link,
                "source": name, "published": published,
                "videos": source_videos(f"{description}\n{content}"),
            })
    return entries


def read_json_entries(name, data, topic, feed_format):
    if not isinstance(data, dict):
        raise ValueError("expected a JSON feed object")
    if feed_format == "json-feed":
        items = data.get("items")
    elif feed_format == "smartrecruiters":
        items = data.get("content")
    else:
        raise ValueError(f"unsupported feed format: {feed_format}")
    if not isinstance(items, list):
        raise ValueError("expected a list of feed entries")

    entries = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if feed_format == "json-feed":
            title = plain_text(item.get("title"))
            summary = plain_text(item.get("content_text") or item.get("summary") or item.get("content_html"))
            url = item.get("url") or ""
            timestamp = item.get("date_published") or item.get("date_modified")
        else:
            company = item.get("company") or {}
            employer, board = company.get("name"), company.get("identifier")
            posting_id = item.get("id")
            if item.get("visibility") != "PUBLIC" or not all((employer, board, posting_id, item.get("name"))):
                continue
            location = item.get("location") or {}
            mode = "Hybrid" if location.get("hybrid") else "Remote" if location.get("remote") else ""
            job_type = (item.get("typeOfEmployment") or {}).get("label")
            title = f"{plain_text(item['name'])} at {plain_text(employer)}"
            summary = " · ".join(part for part in (location.get("fullLocation"), mode, job_type) if part)
            url = f"https://jobs.smartrecruiters.com/{quote(board, safe='')}/{quote(str(posting_id), safe='')}"
            timestamp = item.get("releasedDate")
        try:
            published = datetime.fromisoformat(timestamp or "")
            url = clean_url(url)
        except (TypeError, ValueError):
            continue
        if title and url and published.tzinfo and topic.search(f"{title} {summary}"):
            entries.append({
                "title": title, "summary": summary[:1800], "url": url,
                "source": name, "published": published, "videos": {},
            })
    return entries


def collect(now, seen, *, sources, topic):
    entries = {}
    failures = []
    with ThreadPoolExecutor(max_workers=len(sources)) as pool:
        feeds = {name: pool.submit(read_feed, name, config, topic) for name, config in sources.items()}
        for name, future in feeds.items():
            try:
                config = sources[name]
                lookback_days = 3 if isinstance(config, str) else config.get("lookback_days", 3)
                recent = [
                    entry for entry in future.result()
                    if now - timedelta(days=lookback_days) <= entry["published"] <= now and entry["url"] not in seen
                ]
                for entry in sorted(recent, key=lambda item: item["published"], reverse=True)[:5]:
                    entries.setdefault(entry["url"], entry)
            except (OSError, ValueError, ElementTree.ParseError) as error:
                failures.append(name)
                print(f"Could not read {name}: {error}", file=sys.stderr)
    if len(failures) == len(sources):
        raise SystemExit("All digest feeds failed.")
    return sorted(entries.values(), key=lambda entry: entry["published"], reverse=True)[:35]
