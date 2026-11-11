import json
from pathlib import Path

SOURCES = [
    {
        "id": "investing_001",
        "title": "Introduction to Investing",
        "category": "investing_basics",
        "publisher": "SEC Investor.gov",
        "url": "https://www.investor.gov/introduction-investing",
    },
    {
        "id": "investing_002",
        "title": "Investment Products",
        "category": "investing_basics",
        "publisher": "SEC Investor.gov",
        "url": "https://www.investor.gov/introduction-investing/investing-basics/investment-products",
    },
    {
        "id": "investing_003",
        "title": "Learn About Investment Options",
        "category": "investing_basics",
        "publisher": "SEC Investor.gov",
        "url": "https://www.investor.gov/introduction-investing/investing-basics/save-and-invest/learn-about-investment-options",
    },
    {
        "id": "investing_004",
        "title": "Investing on Your Own",
        "category": "investing_basics",
        "publisher": "SEC Investor.gov",
        "url": "https://www.investor.gov/introduction-investing/getting-started/investing-your-own",
    },
    {
        "id": "investing_005",
        "title": "Mutual Funds",
        "category": "investing_basics",
        "publisher": "SEC Investor.gov",
        "url": "https://www.investor.gov/introduction-investing/investing-basics/investment-products/mutual-funds-and-exchange-traded-funds-etfs/mutual-funds",
    },
    {
        "id": "retirement_001",
        "title": "Designated Roth Accounts",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/retirement-plans-faqs-on-designated-roth-accounts",
    },
{
    "id": "budget_001",
    "title": "Your Money, Your Goals",
    "category": "budgeting",
    "publisher": "Consumer Financial Protection Bureau",
    "url": "https://www.consumerfinance.gov/consumer-tools/educator-tools/your-money-your-goals/",
},
{
    "id": "banking_001",
    "title": "Money Smart",
    "category": "banking",
    "publisher": "Federal Deposit Insurance Corporation",
    "url": "https://www.fdic.gov/consumer-resource-center/money-smart",
},
]

NEW_SOURCES = [
    {
        "id": "credit_001",
        "title": "Understand Your Credit Score",
        "category": "credit",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/understand-your-credit-score/",
    },
    {
        "id": "credit_002",
        "title": "What Is a Credit Card Interest Rate?",
        "category": "credit",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/ask-cfpb/what-is-a-credit-card-interest-rate-what-does-apr-mean-en-44/",
    },
    {
        "id": "credit_003",
        "title": "How Credit Card Interest Is Calculated",
        "category": "credit",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/ask-cfpb/how-does-my-credit-card-company-calculate-the-amount-of-interest-i-owe-en-51/",
    },
    {
        "id": "credit_004",
        "title": "How Credit Card Interest Rates Are Determined",
        "category": "credit",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/ask-cfpb/when-does-a-credit-card-company-decide-what-interest-rate-to-offer-me-on-a-credit-card-en-9/",
    },
    {
        "id": "credit_005",
        "title": "Paying Credit Card Balances and Interest",
        "category": "credit",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/ask-cfpb/if-i-pay-off-my-credit-card-balance-when-it-is-due-is-the-company-allowed-to-charge-me-interest-for-that-month-en-48/",
    },
    {
        "id": "credit_006",
        "title": "Know Before You Owe: Credit Cards",
        "category": "credit",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/data-research/credit-card-data/know-you-owe-credit-cards/",
    },
    {
        "id": "credit_007",
        "title": "Credit Card Key Terms",
        "category": "credit",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/credit-cards/answers/key-terms/",
    },
    {
        "id": "retirement_002",
        "title": "Required Minimum Distributions FAQs",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/retirement-plan-and-ira-required-minimum-distributions-faqs",
    },
    {
        "id": "retirement_003",
        "title": "IRA Distributions and Withdrawals",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/retirement-plans-faqs-regarding-iras-distributions-withdrawals",
    },
    {
        "id": "retirement_004",
        "title": "IRA Frequently Asked Questions",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/retirement-plans-faqs-regarding-iras",
    },
]

MORE_SOURCES = [
    {
        "id": "saving_001",
        "title": "An Essential Guide to Building an Emergency Fund",
        "category": "saving",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/an-essential-guide-to-building-an-emergency-fund/",
    },
    {
        "id": "saving_002",
        "title": "Managing Your Money, Part 2",
        "category": "budgeting",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/paying-for-college/financial-intuition/managing-your-money-part-2/",
    },
    {
        "id": "retirement_005",
        "title": "401(k) and Profit-Sharing Plan Contribution Limits",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-401k-and-profit-sharing-plan-contribution-limits",
    },
    {
        "id": "retirement_006",
        "title": "Choosing a Retirement Plan: 401(k)",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/choosing-a-retirement-plan-401k-plan",
    },
    {
        "id": "retirement_007",
        "title": "401(k) Plan Qualification Requirements",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/plan-sponsor/401k-plan-qualification-requirements",
    },
    {
        "id": "retirement_008",
        "title": "401(k) General Distribution Rules",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/plan-participant-employee/401k-resource-guide-plan-participants-general-distribution-rules",
    },
    {
        "id": "retirement_009",
        "title": "401(k) Plan Overview",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/plan-sponsor/401k-plan-overview",
    },
    {
        "id": "retirement_010",
        "title": "Are You Covered by an Employer Retirement Plan?",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/are-you-covered-by-an-employers-retirement-plan",
    },
    {
        "id": "retirement_011",
        "title": "Retirement Plan FAQs Regarding Contributions",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/retirement-plan-faqs-regarding-contributions",
    },
    {
        "id": "retirement_012",
        "title": "Retirement Topics: Contributions",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-contributions",
    },
]


EXPANSION_SOURCES = [
    # Saving and budgeting
    {
        "id": "saving_003",
        "title": "Your Savings",
        "category": "saving",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/savings/",
    },
    {
        "id": "budget_002",
        "title": "Budgeting",
        "category": "budgeting",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/budgeting/",
    },
    {
        "id": "budget_003",
        "title": "Financial Well-Being",
        "category": "financial_planning",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/financial-well-being/",
    },
    {
        "id": "credit_008",
        "title": "Credit Reports and Scores",
        "category": "credit",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/",
    },
    {
        "id": "debt_001",
        "title": "Debt Collection",
        "category": "debt",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/debt-collection/",
    },
    {
        "id": "debt_002",
        "title": "Student Loans",
        "category": "debt",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/student-loans/",
    },
    {
        "id": "banking_002",
        "title": "Bank Accounts and Services",
        "category": "banking",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/bank-accounts/",
    },
    {
        "id": "mortgage_001",
        "title": "Buying a House",
        "category": "mortgage",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/owning-a-home/",
    },
    {
        "id": "mortgage_002",
        "title": "Mortgage",
        "category": "mortgage",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/mortgages/",
    },
    {
        "id": "credit_009",
        "title": "Credit Cards",
        "category": "credit",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/credit-cards/",
    },
    # IRS educational sources
    {
        "id": "retirement_013",
        "title": "Retirement Topics: IRA Contribution Limits",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-ira-contribution-limits",
    },
    {
        "id": "retirement_014",
        "title": "Traditional and Roth IRAs",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/traditional-and-roth-iras",
    },
    {
        "id": "retirement_015",
        "title": "Roth Comparison Chart",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/roth-comparison-chart",
    },
    {
        "id": "retirement_016",
        "title": "Retirement Topics: Beneficiary",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-beneficiary",
    },
    {
        "id": "retirement_017",
        "title": "Retirement Topics: Vesting",
        "category": "retirement",
        "publisher": "IRS",
        "url": "https://www.irs.gov/retirement-plans/plan-participant-employee/retirement-topics-vesting",
    },
    # More personal finance education
    {
        "id": "credit_010",
        "title": "Disputing Errors on Credit Reports",
        "category": "credit",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/credit-reports-and-scores/answers/key-terms/",
    },
    {
        "id": "debt_003",
        "title": "Debt Collection Answers",
        "category": "debt",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/debt-collection/answers/key-terms/",
    },
    {
        "id": "saving_004",
        "title": "Savings Answers",
        "category": "saving",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/savings/answers/key-terms/",
    },
    {
        "id": "banking_003",
        "title": "Bank Account Answers",
        "category": "banking",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/bank-accounts/answers/key-terms/",
    },
    {
        "id": "mortgage_003",
        "title": "Mortgage Answers",
        "category": "mortgage",
        "publisher": "CFPB",
        "url": "https://www.consumerfinance.gov/consumer-tools/mortgages/answers/key-terms/",
    },
]

INVESTING_SOURCES = [
    {
        "id": "investing_006",
        "title": "Stocks vs. ETFs vs. Mutual Funds",
        "category": "investing_basics",
        "publisher": "Fidelity",
        "url": "https://www.fidelity.com/learning-center/trading-investing/stocks-vs-etfs-vs-mutual-funds",
    },
    {
        "id": "investing_007",
        "title": "Bonds vs. Bond Funds",
        "category": "investing_basics",
        "publisher": "Fidelity",
        "url": "https://www.fidelity.com/learning-center/investment-products/mutual-funds/bond-vs-bond-funds",
    },
    {
        "id": "investing_008",
        "title": "Index Funds",
        "category": "investing_basics",
        "publisher": "Charles Schwab",
        "url": "https://www.schwab.com/schwab-index-funds-etfs",
    },
    {
        "id": "investing_009",
        "title": "The Basics of Selecting Investments",
        "category": "investing_basics",
        "publisher": "FINRA",
        "url": "https://syndication.finra.org/content/basics-selecting-investments",
    },
    {
        "id": "investing_010",
        "title": "Why Diversify?",
        "category": "diversification",
        "publisher": "Fidelity",
        "url": "https://www.fidelity.com/learning-center/investment-products/mutual-funds/why-diversify",
    },
    {
        "id": "investing_011",
        "title": "What Is Portfolio Diversification?",
        "category": "diversification",
        "publisher": "Fidelity",
        "url": "https://www.fidelity.com/learning-center/investment-products/mutual-funds/diversification",
    },
    {
        "id": "investing_012",
        "title": "3 Steps to Diversify Your Investment Portfolio",
        "category": "diversification",
        "publisher": "Fidelity",
        "url": "https://www.fidelity.com/learning-center/wealth-management-insights/how-to-build-a-diversified-investment-portfolio",
    },
    {
        "id": "investing_013",
        "title": "Portfolio Management Checklist",
        "category": "portfolio_management",
        "publisher": "Charles Schwab",
        "url": "https://www.schwab.com/learn/story/portfolio-management-checklist",
    },
    {
        "id": "investing_014",
        "title": "How to Build a Portfolio with ETFs",
        "category": "portfolio_management",
        "publisher": "Fidelity",
        "url": "https://www.fidelity.com/learning-center/trading-investing/how-to-build-etf-portfolio",
    },
    {
        "id": "investing_015",
        "title": "3 Ways to Build an All-ETF Portfolio",
        "category": "portfolio_management",
        "publisher": "Charles Schwab",
        "url": "https://www.schwab.com/learn/story/3-ways-to-build-all-etf-portfolio",
    },
]

SOURCES.extend(INVESTING_SOURCES)

SOURCES.extend(EXPANSION_SOURCES)

SOURCES.extend(MORE_SOURCES)

SOURCES.extend(NEW_SOURCES)
manifest_path = Path("src/data/article_sources.json")
manifest_path.parent.mkdir(parents=True, exist_ok=True)

# Preserve existing sources and downloaded article IDs.
existing = []
if manifest_path.exists():
    existing = json.loads(manifest_path.read_text(encoding="utf-8"))

by_id = {article["id"]: article for article in existing}

for source in SOURCES:
    if source["id"] in by_id:
        by_id[source["id"]] = {
            **by_id[source["id"]],
            **source,
        }
    else:
        by_id[source["id"]] = {
            **source,
            "review_status": "pending",
        }

manifest_path.write_text(
    json.dumps(list(by_id.values()), indent=2),
    encoding="utf-8",
)

print(f"Manifest contains {len(by_id)} articles.")
