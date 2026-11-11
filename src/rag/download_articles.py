import json
import time
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import requests
import trafilatura

MANIFEST_PATH = Path("src/data/article_sources.json")
OUTPUT_DIR = Path("src/data/knowledge_base/articles")

USER_AGENT = "FinnieEducationalResearchBot/1.0"


ROBOTS_CACHE = {}
def robots_allowed(url: str) -> bool:
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    # Reuse one robots policy for all article URLs on the same site.
    if robots_url not in ROBOTS_CACHE:
        try:
            response = requests.get(robots_url, timeout=15)
            response.raise_for_status()

            parser = RobotFileParser()
            parser.parse(response.text.splitlines())

            ROBOTS_CACHE[robots_url] = parser

        except requests.RequestException as exc:
            print(f"Cannot verify robots policy: {exc}")
            ROBOTS_CACHE[robots_url] = None

    parser = ROBOTS_CACHE[robots_url]

    if parser is None:
        return False

    return parser.can_fetch("FinnieEducationalBot", url)
def download_article(article):
    url = article["url"]

    if not robots_allowed(url):
        print(f"Skipped (robots restrictions): {url}")
        return False

    response = requests.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=20,
    )
    response.raise_for_status()

    # Extract article text from HTML so navigation and page chrome stay out of retrieval.
    content = trafilatura.extract(
        response.text,
        include_comments=False,
        include_tables=True,
    )

    if not content or len(content.strip()) < 300:
        print(f"Skipped (insufficient content): {url}")
        return False

    # Keep the manifest fields alongside the downloaded text and retrieval date.
    record = {
        **article,
        "retrieved_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "content": content,
    }

    output_path = OUTPUT_DIR / f"{article['id']}.json"
    output_path.write_text(
        json.dumps(record, indent=2),
        encoding="utf-8",
    )

    print(f"Saved: {article['title']}")
    return True


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    articles = json.loads(
        MANIFEST_PATH.read_text(encoding="utf-8")
    )

    successful = 0

    for article in articles:
        try:
            if download_article(article):
                successful += 1
        except Exception as exc:
            print(f"Failed: {article['url']}: {exc}")

        time.sleep(2)

    print(
        f"\nSuccessfully downloaded "
        f"{successful}/{len(articles)} articles"
    )


if __name__ == "__main__":
    main()
