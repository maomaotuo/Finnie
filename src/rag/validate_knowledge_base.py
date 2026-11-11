import json
from pathlib import Path
from urllib.parse import urlparse

MANIFEST = Path("src/data/article_sources.json")
ARTICLE_DIR = Path("src/data/knowledge_base/articles")


def main():
    sources = json.loads(MANIFEST.read_text(encoding="utf-8"))

    ids = [item["id"] for item in sources]
    urls = [item["url"].rstrip("/") for item in sources]

    assert len(ids) == len(set(ids)), "Duplicate article IDs"
    assert len(urls) == len(set(urls)), "Duplicate URLs"

    indexed_ready = 0

    for article in sources:
        article_id = article["id"]
        path = ARTICLE_DIR / f"{article_id}.json"

        if not urlparse(article["url"]).scheme.startswith("http"):
            print(f"INVALID URL: {article_id}")
            continue

        if not path.exists():
            print(f"NOT DOWNLOADED: {article_id}")
            continue

        try:
            content = json.loads(path.read_text(encoding="utf-8"))
            text = content.get("content", "").strip()

            if len(text) < 1000:
                print(f"TOO SHORT: {article_id} ({len(text)} chars)")
                continue

            indexed_ready += 1
            print(f"READY: {article_id} ({len(text)} chars)")
        except (OSError, ValueError) as exc:
            print(f"INVALID ARTICLE: {article_id}: {exc}")

    print("\n--- Knowledge Base Summary ---")
    print("Manifest entries:", len(sources))
    print("Content-ready articles:", indexed_ready)
    print("Target:", 60)
    print("Remaining content-ready articles needed:", max(0, 60 - indexed_ready))


if __name__ == "__main__":
    main()
