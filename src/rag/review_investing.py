import json
from pathlib import Path
from collections import Counter

manifest_path = Path("src/data/article_sources.json")

candidate_ids = {
    "investing_006",
    "investing_007",
    "investing_009",
    "investing_010",
    "investing_011",
    "investing_012",
    "investing_014",
}

excluded_ids = {
    "investing_008",
    "investing_013",
    "investing_015",
}

articles = json.loads(
    manifest_path.read_text(encoding="utf-8")
)

for article in articles:
    article_id = article["id"]

    if article_id in candidate_ids:
        article["review_status"] = "candidate"
    elif article_id in excluded_ids:
        article["review_status"] = "excluded"

manifest_path.write_text(
    json.dumps(articles, indent=2),
    encoding="utf-8",
)

counts = Counter(
    article.get("review_status", "pending")
    for article in articles
)

print("Review status summary:")
for status, count in sorted(counts.items()):
    print(f"{status}: {count}")
