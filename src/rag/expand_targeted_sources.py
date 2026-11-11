import json
import re
import time
import certifi
import requests
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.robotparser import RobotFileParser

MANIFEST = Path("src/data/article_sources.json")
USER_AGENT = "FinnieResearchBot/1.0"
LIMIT = 40

SEEDS = [
    ("https://www.fidelity.com/learning-center/personal-finance/saving-and-budgeting-money", "budgeting"),
    ("https://www.fidelity.com/learning-center/personal-finance/money-management", "financial_goals"),
    ("https://www.consumerfinance.gov/consumer-tools/credit-cards/answers/", "credit"),
]

ALLOWED_HOSTS = {
    "www.fidelity.com",
    "www.consumerfinance.gov",
}

SKIP_WORDS = (
    "login", "sign in", "privacy", "contact",
    "podcast", "video", "webinar", "calculator",
    "training", "toolkit", "glossary",
)

session = requests.Session()
session.headers.update({"User-Agent": USER_AGENT})
session.verify = certifi.where()

robots_cache = {}


def allowed(url):
    parsed = urlparse(url)
    host = parsed.netloc.lower()

    if parsed.scheme != "https" or host not in ALLOWED_HOSTS:
        return False

    if host not in robots_cache:
        robots_url = f"https://{host}/robots.txt"
        try:
            response = session.get(robots_url, timeout=15)
            response.raise_for_status()
            parser = RobotFileParser()
            parser.parse(response.text.splitlines())
            robots_cache[host] = parser
        except requests.RequestException:
            robots_cache[host] = None

    parser = robots_cache[host]
    return parser is not None and parser.can_fetch(USER_AGENT, url)


def fetch(url):
    if not allowed(url):
        print("Robots unavailable or disallowed:", url)
        return None

    try:
        response = session.get(url, timeout=20)
        response.raise_for_status()
        time.sleep(0.5)
        return BeautifulSoup(response.text, "html.parser")
    except requests.RequestException as exc:
        print("Fetch failed:", url, exc)
        return None


def normalize(url):
    url = urldefrag(url)[0]
    parsed = urlparse(url)
    return parsed._replace(
        query="",
        path=parsed.path.rstrip("/") or "/"
    ).geturl()


def category_for(title, default):
    text = title.lower()
    rules = {
        "investing": ["invest", "stock", "bond", "etf", "portfolio", "fund"],
        "saving": ["saving", "emergency fund"],
        "budgeting": ["budget", "spending", "expenses"],
        "debt": ["debt", "loan", "borrow"],
        "credit": ["credit", "apr", "interest rate"],
        "financial_goals": ["financial goal", "financial plan"],
        "banking": ["bank account", "checking account"],
        "mortgage": ["mortgage", "home loan"],
    }
    for category, words in rules.items():
        if any(word in text for word in words):
            return category
    return default


def article_link(url):
    path = urlparse(url).path.lower()
    if "/ask-cfpb/" in path:
        return True
    if "/learning-center/personal-finance/" in path:
        return len(path.strip("/").split("/")) >= 3
    if "/viewpoints/personal-finance/" in path:
        return True
    return False


data = json.loads(MANIFEST.read_text())
articles = data if isinstance(data, list) else data["articles"]

existing = {
    normalize(a["url"])
    for a in articles
    if a.get("url")
}

used_ids = {
    a["id"] for a in articles
}

next_number = 1
added = 0

for seed, default_category in SEEDS:
    if added >= LIMIT:
        break

    print("\nScanning:", seed)
    soup = fetch(seed)
    if soup is None:
        continue

    for link in soup.select("a[href]"):
        if added >= LIMIT:
            break

        title = " ".join(link.get_text(" ", strip=True).split())
        url = normalize(urljoin(seed, link["href"]))

        if len(title) < 18 or len(title) > 130:
            continue
        if any(word in title.lower() for word in SKIP_WORDS):
            continue
        if not article_link(url):
            continue
        if url in existing:
            continue
        if not allowed(url):
            continue

        while f"target_{next_number:03d}" in used_ids:
            next_number += 1

        article_id = f"target_{next_number:03d}"
        next_number += 1

        articles.append({
            "id": article_id,
            "title": title,
            "category": category_for(title, default_category),
            "publisher": urlparse(url).netloc,
            "url": url,
            "review_status": "needs_review",
        })

        existing.add(url)
        used_ids.add(article_id)
        added += 1
        print(f"ADDED {article_id}: {title}")

MANIFEST.write_text(
    json.dumps(data, indent=2, ensure_ascii=False) + "\n"
)

print("\nNew sources:", added)
print("Manifest total:", len(articles))
print("Candidates:", sum(
    a.get("review_status") == "candidate"
    for a in articles
))
