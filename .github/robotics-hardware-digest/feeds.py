"""Read and filter robotics news feeds."""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta
from email.utils import parsedate_to_datetime
from html import unescape
import re
import sys
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree


SOURCES = {
    "arXiv Robotics": "https://rss.arxiv.org/rss/cs.RO",
    "arXiv Computer Vision": "https://rss.arxiv.org/rss/cs.CV",
    "arXiv Signal Processing": "https://rss.arxiv.org/rss/eess.SP",
    "CMU Robotics Institute": "https://www.ri.cmu.edu/news/feed/",
    "Berkeley AI Research": "https://bair.berkeley.edu/blog/feed.xml",
    "RealSense": "https://www.realsenseai.com/feed/",
    "e-con Systems": "https://www.e-consystems.com/blog/camera/feed/",
    "Hesai": "https://www.hesaitech.com/feed/",
    "Sharpa": "https://www.sharpa.com/blogs/news.atom",
    "Motion Control Tips": "https://www.motioncontroltips.com/feed/",
    "NVIDIA Robotics": "https://blogs.nvidia.com/blog/category/robotics/feed/",
    "NVIDIA Developer": "https://developer.nvidia.com/blog/feed/",
    "AMD News Releases": "https://ir.amd.com/news-events/press-releases/rss",
    "Intel News Releases": "https://www.intc.com/news-events/press-releases/rss",
    "Raspberry Pi": "https://www.raspberrypi.com/news/feed/",
    "STMicroelectronics": "https://blog.st.com/feed/",
    "CNX Software": "https://www.cnx-software.com/feed/",
    "IEEE Spectrum Robotics": "https://spectrum.ieee.org/feeds/topic/robotics.rss",
    "The Robot Report": "https://www.therobotreport.com/feed/",
}
HARDWARE = re.compile(
    r"\b(?:sensors?|sensing|li[ -]?dars?|radars?|depth cameras?|stereo vision|"
    r"rgb(?:[ -]?d)?|time[ -]of[ -]flight|tof|tactile|vision modules?|cameras?|"
    r"grippers?|actuat\w+|servos?|motors?|motor drives?|gearboxes|encoders?|"
    r"inertial|imus?|robotic hands?|end[ -]effectors?|[gcn]pus?|fpgas?|socs?|"
    r"embedded processors?|edge accelerators?|jetson|system[ -]on[ -]modules?)\b", re.I
)
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


def read_feed(source):
    name, url = source
    request = Request(url, headers={"User-Agent": "RoboticsHardwareDigest/1.0"})
    with urlopen(request, timeout=20) as response:
        root = ElementTree.fromstring(response.read(4_000_000))
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
        if title and link and published.tzinfo and HARDWARE.search(title + " " + summary):
            entries.append({
                "title": title, "summary": summary[:1800], "url": link,
                "source": name, "published": published,
                "videos": source_videos(f"{description}\n{content}"),
            })
    return entries


def collect(now, seen):
    entries = {}
    failures = []
    with ThreadPoolExecutor(max_workers=len(SOURCES)) as pool:
        feeds = {name: pool.submit(read_feed, (name, url)) for name, url in SOURCES.items()}
        for name, future in feeds.items():
            try:
                recent = [
                    entry for entry in future.result()
                    if now - timedelta(hours=72) <= entry["published"] <= now and entry["url"] not in seen
                ]
                for entry in sorted(recent, key=lambda item: item["published"], reverse=True)[:5]:
                    entries.setdefault(entry["url"], entry)
            except (OSError, ValueError, ElementTree.ParseError) as error:
                failures.append(name)
                print(f"Could not read {name}: {error}", file=sys.stderr)
    if len(failures) == len(SOURCES):
        raise SystemExit("All digest feeds failed.")
    return sorted(entries.values(), key=lambda entry: entry["published"], reverse=True)[:35]
