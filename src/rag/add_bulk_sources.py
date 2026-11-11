import json
from pathlib import Path

path = Path("src/data/article_sources.json")

sources = [
    ("retirement_018", "Retirement Topics - Contributions", "retirement", "IRS",
     "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-contributions"),
    ("retirement_019", "Rollovers of Retirement Plan and IRA Distributions", "retirement", "IRS",
     "https://www.irs.gov/retirement-plans/plan-participant-employee/rollovers-of-retirement-plan-and-ira-distributions"),
    ("retirement_020", "Topic 413 - Rollovers from Retirement Plans", "retirement", "IRS",
     "https://www.irs.gov/taxtopics/tc413"),
    ("saving_002", "Saving Each Payday", "saving", "CFPB",
     "https://www.consumerfinance.gov/consumer-tools/educator-tool/youth-financial-education/teach/activities/saving-each-payday/"),
    ("budgeting_001", "Learning About Budgets", "budgeting", "CFPB",
     "https://www.consumerfinance.gov/consumer-tools/educator-tool/youth-financial-education/teach/activities/learning-about-budgets/"),
    ("budgeting_002", "Creating a Monthly Household Budget", "budgeting", "CFPB",
     "https://www.consumerfinance.gov/consumer-tools/educator-tool/youth-financial-education/teach/activities/creating-monthly-household-budget/"),
    ("budgeting_003", "Analyzing Budgets", "budgeting", "CFPB",
     "https://www.consumerfinance.gov/consumer-tools/educator-tool/youth-financial-education/teach/activities/analyzing-budgets/"),
]

data = json.loads(path.read_text())
articles = data if isinstance(data, list) else data["articles"]

existing_ids = {a["id"] for a in articles}
existing_urls = {a.get("url") for a in articles}

added = 0

for article_id, title, category, publisher, url in sources:
    if article_id in existing_ids or url in existing_urls:
        continue

    articles.append({
        "id": article_id,
        "title": title,
        "category": category,
        "publisher": publisher,
        "url": url,
        "review_status": "needs_review",
    })

    existing_ids.add(article_id)
    existing_urls.add(url)
    added += 1

path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")

print(f"Added {added} sources")
print(f"Total manifest entries: {len(articles)}")
