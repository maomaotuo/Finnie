import json
from pathlib import Path

path = Path("src/data/article_sources.json")
data = json.loads(path.read_text())

articles = data if isinstance(data, list) else data["articles"]

decisions = {
    "retirement_019": "candidate",
    "retirement_020": "candidate",
    "budgeting_001": "excluded",
    "budgeting_002": "excluded",
    "budgeting_003": "excluded",
    "saving_002": "needs_review",
}

for article in articles:
    article_id = article["id"]
    if article_id in decisions:
        article["review_status"] = decisions[article_id]
        print(article_id, "->", decisions[article_id])

path.write_text(
    json.dumps(data, indent=2, ensure_ascii=False) + "\n"
)

from collections import Counter

print("\nReview status totals:")
print(Counter(a.get("review_status") for a in articles))
