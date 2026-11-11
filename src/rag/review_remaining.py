import json
from pathlib import Path
from collections import Counter

path = Path("src/data/article_sources.json")
data = json.loads(path.read_text())
articles = data if isinstance(data, list) else data["articles"]

candidate_ids = {
    "retirement_006",
    "retirement_009",
    "retirement_010",
    "retirement_012",
    "retirement_015",
    "debt_002",
}

excluded_ids = {
    "investing_001",
    "investing_002",
    "investing_003",
    "investing_004",
    "investing_005",
    "credit_002",
    "credit_005",
    "retirement_011",
    "credit_010",
}

for article in articles:
    article_id = article["id"]

    if article_id in candidate_ids:
        article["review_status"] = "candidate"
    elif article_id in excluded_ids:
        article["review_status"] = "excluded"
    else:
        continue

    print(article_id, "->", article["review_status"])

path.write_text(
    json.dumps(data, indent=2, ensure_ascii=False) + "\n"
)

print("\nFinal review totals:")
print(Counter(a.get("review_status") for a in articles))
