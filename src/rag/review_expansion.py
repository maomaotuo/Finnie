import json
from pathlib import Path

manifest_path = Path("src/data/article_sources.json")

candidate_ids = {
    "banking_003",
    "debt_001",
    "debt_003",
    "mortgage_003",
    "retirement_013",
    "retirement_014",
    "retirement_016",
    "retirement_017",
}

needs_review_ids = {
    "debt_002",
    "retirement_015",
    "credit_010",
}

excluded_ids = {
    "budget_003",
    "credit_008",
    "credit_009",
    "banking_002",
    "mortgage_001",
    "mortgage_002",
    "saving_003",
    "budget_002",
    "saving_004",
}

articles = json.loads(
    manifest_path.read_text(encoding="utf-8")
)

for article in articles:
    article_id = article["id"]

    if article_id in candidate_ids:
        article["review_status"] = "candidate"
    elif article_id in needs_review_ids:
        article["review_status"] = "needs_review"
    elif article_id in excluded_ids:
        article["review_status"] = "excluded"

manifest_path.write_text(
    json.dumps(articles, indent=2),
    encoding="utf-8",
)

from collections import Counter

counts = Counter(
    article.get("review_status", "pending")
    for article in articles
)

print("Review status summary:")
for status, count in sorted(counts.items()):
    print(f"{status}: {count}")
