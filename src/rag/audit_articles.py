import json
from pathlib import Path

ARTICLE_DIR = Path("src/data/knowledge_base/articles")

EXCLUDED_IDS = {"budget_001", "banking_001"}


def main():
    for path in sorted(ARTICLE_DIR.glob("*.json")):
        article = json.loads(path.read_text(encoding="utf-8"))

        article_id = article["id"]
        content = article.get("content", "").strip()

        if article_id in EXCLUDED_IDS:
            continue

        if len(content) < 1000:
            continue

        print(f"\n{'=' * 60}")
        print("ID:", article_id)
        print("Title:", article.get("title"))
        print("Category:", article.get("category"))
        print("Characters:", len(content))
        print("Preview:", content[:350].replace("\n", " "))


if __name__ == "__main__":
    main()
