import json
from pathlib import Path
from collections import Counter

path = Path("src/data/article_sources.json")
data = json.loads(path.read_text())
articles = data if isinstance(data, list) else data["articles"]

decisions = {
    "bulk_001": "excluded",
    "bulk_002": "excluded",
    "bulk_003": "excluded",
    "bulk_004": "candidate",
    "bulk_005": "excluded",
}

for article in articles:
    article_id = article["id"]

    if article_id in decisions:
        article["review_status"] = decisions[article_id]
        print(article_id, "->", decisions[article_id])

path.write_text(
    json.dumps(data, indent=2, ensure_ascii=False) + "\n"
)

print("\nReview totals:")
print(Counter(a.get("review_status") for a in articles))
