import json
import re
import ssl
import certifi
import urllib.request
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag

MANIFEST = Path("src/data/article_sources.json")
TARGET_NEW = 31

SEEDS = [
    "https://www.investor.gov/introduction-investing",
    "https://www.investor.gov/introduction-investing/investing-basics/save-and-invest",
    "https://www.investor.gov/introduction-investing/investing-basics/investment-products",
    "https://www.consumerfinance.gov/consumer-tools/",
    "https://www.consumerfinance.gov/consumer-tools/educator-tool/your-money-your-goals/toolkit/",
]

KEYWORDS = {
    "investing": [
        "invest", "stock", "bond", "fund", "portfolio",
        "diversif", "asset-allocation", "risk", "fee",
    ],
    "budgeting": [
        "budget", "spending", "cash-flow", "income",
    ],
    "saving": [
        "saving", "savings", "emergency",
    ],
    "credit": [
        "credit", "credit-card", "credit-report",
    ],
    "debt": [
        "debt", "loan", "repay",
    ],
    "financial_goals": [
        "goal", "financial-plan", "planning",
    ],
    "banking": [
        "bank", "checking", "deposit",
    ],
    "mortgage": [
        "mortgage", "homebuy", "buying-a-house",
    ],
}


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.href = None
        self.label = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.label = []

    def handle_data(self, data):
        if self.href is not None:
            self.label.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href:
            self.links.append(
                (self.href, " ".join(self.label).strip())
            )
            self.href = None


def fetch(url):
    req = urllib.request.Request(
        url,
        headers={"User-Agent": "FinnieResearchBot/1.0"}
    )
    with urllib.request.urlopen(req, timeout=15) as response:
        return response.read().decode("utf-8", errors="replace")



def fetch(url):
    context = ssl.create_default_context(
        cafile=certifi.where()
    )

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "FinnieResearchBot/1.0"
        }
    )

    with urllib.request.urlopen(
        req,
        timeout=15,
        context=context
    ) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )



def allowed(url):
    parsed = urlparse(url)
    host = parsed.hostname or ""
    path = parsed.path.lower()
    if parsed.scheme != "https":
        return False

    if host == "www.investor.gov":
        return path.startswith("/introduction-investing/")

    if host == "www.consumerfinance.gov":
        return (
            path.startswith("/consumer-tools/")
            and "/teach/activities/" not in path
            and "/educator-tool/" not in path
        )

    return False


data = json.loads(MANIFEST.read_text())
articles = data if isinstance(data, list) else data["articles"]

existing_urls = {
    a.get("url", "").rstrip("/") for a in articles
}
existing_ids = {a["id"] for a in articles}

discovered = []

for seed in SEEDS:
    print("Discovering:", seed)

    try:
        parser = LinkParser()
        parser.feed(fetch(seed))
    except Exception as exc:
        print("  Skipped:", exc)
        continue

    for href, title in parser.links:
        url = urldefrag(urljoin(seed, href))[0].rstrip("/")
        category = classify(url, title)

        if not allowed(url) or not category:
            continue
        if url in existing_urls:
            continue
        if not title or len(title) < 12:
            continue

        discovered.append((url, title, category))
        existing_urls.add(url)

# Prefer a balanced mix of subjects rather than only investing.
selected = []
categories = list(KEYWORDS)

while discovered and len(selected) < TARGET_NEW:
    made_progress = False

    for category in categories:
        for i, item in enumerate(discovered):
            if item[2] == category:
                selected.append(discovered.pop(i))
                made_progress = True
                break

        if len(selected) >= TARGET_NEW:
            break

    if not made_progress:
        break

added = 0
next_number = 1

for url, title, category in selected:
    while f"bulk_{next_number:03d}" in existing_ids:
        next_number += 1

    article_id = f"bulk_{next_number:03d}"
    existing_ids.add(article_id)

    articles.append({
        "id": article_id,
        "title": re.sub(r"\s+", " ", title),
        "category": category,
        "publisher": (
            "SEC Investor.gov"
            if "investor.gov" in url else "CFPB"
        ),
        "url": url,
        "review_status": "needs_review",
    })

    print(f"ADDED {article_id}: {title} [{category}]")
    added += 1

MANIFEST.write_text(
    json.dumps(data, indent=2, ensure_ascii=False) + "\n"
)

print(f"\nAdded: {added}")
print(f"Manifest total: {len(articles)}")
print(f"Curated candidates: {sum(a.get('review_status') == 'candidate' for a in articles)}")
