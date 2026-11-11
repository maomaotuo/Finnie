import json
from pathlib import Path

MANIFEST = Path("src/data/article_sources.json")

KEEP = {
    "credit_001", "credit_003", "credit_004", "credit_007",
    "retirement_001", "retirement_002", "retirement_003",
    "retirement_004", "retirement_005", "retirement_008",
    "saving_001",
}

EXCLUDE = {
    "budget_001", "banking_001",
    "credit_006", "retirement_007",
}


def main():
    sources = json.loads(MANIFEST.read_text(encoding="utf-8"))

    for source in sources:
        article_id = source["id"]

        if article_id in KEEP:
            source["review_status"] = "candidate"
        elif article_id in EXCLUDE:
            source["review_status"] = "excluded"
        else:
            source["review_status"] = "needs_review"

    MANIFEST.write_text(
        json.dumps(sources, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    print("Updated review statuses:")
    for status in ("candidate", "needs_review", "excluded"):
        count = sum(
            s["review_status"] == status for s in sources
        )
        print(f"{status}: {count}")


if __name__ == "__main__":
    main()
