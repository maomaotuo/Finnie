import json
from pathlib import Path
from collections import Counter

path = Path("src/data/article_sources.json")
data = json.loads(path.read_text())
articles = data if isinstance(data, list) else data["articles"]

accepted = {
    9, 10, 11, 12, 13, 14, 15, 16, 17, 18,
    19, 20, 21, 22, 23, 24, 25, 26, 27,
    31, 32, 34, 38, 39, 40
}

for article in articles:
    article_id = article["id"]

    if not article_id.startswith("target_"):
        continue

    number = int(article_id.split("_")[1])

    if number in accepted:
        article["review_status"] = "candidate"
    else:
        article["review_status"] = "excluded"

path.write_text(
    json.dumps(data, indent=2, ensure_ascii=False) + "\n"
)

print("Review totals:")
print(Counter(
    a.get("review_status") for a in articles
))
