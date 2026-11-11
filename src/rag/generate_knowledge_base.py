from pathlib import Path
import json

OUTPUT_DIR = Path("src/data/knowledge_base/topics")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TOPICS = [
    {
        "id": "basics_001",
        "title": "What Are Stocks?",
        "category": "investing_basics",
        "source_url": "",
        "content": """# What Are Stocks?

A stock represents an ownership interest in a company. Investors who own shares may benefit when the company grows and its share price rises. Some companies also distribute part of their earnings to shareholders through dividends.

Stock prices can fluctuate due to company performance, economic conditions, interest rates, and investor expectations.

## Main Risks

Individual stocks expose investors to company-specific risks. A company may perform poorly, reduce dividends, or lose substantial value.

## Key Takeaway

Stocks can provide long-term growth opportunities, but their returns are not guaranteed.
"""
    },
    {
        "id": "basics_002",
        "title": "What Are Bonds?",
        "category": "investing_basics",
        "source_url": "",
        "content": """# What Are Bonds?

A bond is a debt security issued by a government, corporation, or other organization. When investors purchase bonds, they generally lend money to the issuer in exchange for interest payments and repayment of principal according to the bond's terms.

## Bond Risks

- Interest-rate risk: Bond prices often decline when market interest rates rise.
- Credit risk: An issuer may fail to make promised payments.
- Inflation risk: Inflation can reduce the purchasing power of future payments.

## Key Takeaway

Bonds may provide income and diversification, but they are not risk-free.
"""
    },
    {
        "id": "basics_003",
        "title": "What Is an ETF?",
        "category": "investing_basics",
        "source_url": "",
        "content": """# What Is an ETF?

An exchange-traded fund (ETF) is an investment fund whose shares trade on an exchange. ETFs can hold stocks, bonds, or other assets.

## Benefits

- Some ETFs provide broad diversification.
- Many ETFs have relatively low operating expenses.
- ETF shares can generally be bought or sold during market hours.

## Risks

An ETF can lose value. Its diversification depends on its underlying holdings. Some ETFs concentrate on a single industry, country, or strategy.

## Expense Ratios

An expense ratio represents a fund's annual operating expenses as a percentage of its assets.

## Key Takeaway

ETFs are investment vehicles, not guarantees of diversification or positive returns.
"""
    },
    {
        "id": "basics_004",
        "title": "What Is a Mutual Fund?",
        "category": "investing_basics",
        "source_url": "",
        "content": """# What Is a Mutual Fund?

A mutual fund pools money from investors and invests according to a defined investment strategy. It may hold stocks, bonds, or other securities.

Unlike ETFs, traditional mutual fund transactions generally execute at the fund's next calculated net asset value rather than trading continuously on an exchange.

## Important Considerations

- Investment objective and strategy
- Expense ratio and other fees
- Diversification
- Investment risks
- Tax consequences

## Key Takeaway

Mutual funds offer access to professionally managed portfolios, but investors should review fees, holdings, and risks.
"""
    },
    {
        "id": "basics_005",
        "title": "Diversification and Asset Allocation",
        "category": "portfolio",
        "source_url": "",
        "content": """# Diversification and Asset Allocation

Diversification means spreading investments across different assets to reduce concentration risk.

Asset allocation means deciding how much of a portfolio to invest in categories such as stocks, bonds, and cash.

## Example

A portfolio with 60% stocks and 40% bonds has a different risk profile from one with 100% stocks.

## Important Limitations

Diversification cannot eliminate market risk or guarantee against losses. Holding several investments that behave similarly may provide limited diversification.

## Rebalancing

Rebalancing adjusts portfolio holdings toward a chosen target allocation. It may involve transaction costs and taxes.

## Key Takeaway

Portfolio construction should consider risk tolerance, time horizon, and financial goals.
"""
    },
    {
        "id": "basics_006",
        "title": "Compound Interest",
        "category": "financial_planning",
        "source_url": "",
        "content": """# Compound Interest

Compound interest occurs when interest is earned on both the original principal and previously accumulated interest.

## Formula

Future Value = Principal × (1 + Rate / Compounding Periods) ^ (Compounding Periods × Years)

## Example

If $1,000 earns a hypothetical 5% annual return compounded annually for 10 years:

Future Value = 1000 × (1.05)^10 ≈ $1,628.89

This example assumes a constant rate and no taxes, fees, or withdrawals.

## Key Takeaway

Compounding can increase long-term growth, but actual investment returns fluctuate and are not guaranteed.
"""
    },
    {
        "id": "basics_007",
        "title": "Understanding 401(k) Plans",
        "category": "retirement",
        "source_url": "",
        "content": """# Understanding 401(k) Plans

A 401(k) is an employer-sponsored retirement savings plan. Eligible employees may contribute part of their compensation through payroll deductions.

## Traditional Contributions

Traditional pre-tax contributions generally reduce current taxable income. Distributions are generally taxable when withdrawn.

## Designated Roth Contributions

Designated Roth contributions are generally made with after-tax income. Qualified distributions may be tax-free when applicable requirements are met.

## Employer Matching

Some employers contribute additional amounts based on employee contributions or other plan rules.

## Key Takeaway

401(k) rules, contribution limits, withdrawal restrictions, and employer features depend on the plan and applicable tax law.
"""
    },
    {
        "id": "basics_008",
        "title": "Traditional IRA vs Roth IRA",
        "category": "retirement",
        "source_url": "",
        "content": """# Traditional IRA vs Roth IRA

Individual retirement arrangements (IRAs) are accounts designed to support retirement savings.

## Traditional IRA

Contributions may be tax-deductible depending on income, filing status, and retirement plan coverage. Distributions are generally taxable to the extent they represent pre-tax amounts and earnings.

## Roth IRA

Contributions are not tax-deductible. Qualified distributions can be tax-free.

## Important Differences

- Tax treatment of contributions
- Eligibility and income limits
- Withdrawal rules
- Required minimum distribution rules
- Contribution limits

## Key Takeaway

The appropriate account depends on individual circumstances. A Roth IRA is different from a designated Roth account inside a 401(k) or similar employer plan.
"""
    },
    {
        "id": "basics_009",
        "title": "Emergency Funds",
        "category": "financial_planning",
        "source_url": "",
        "content": """# Emergency Funds

An emergency fund is money reserved for unexpected expenses or interruptions in income.

Examples include urgent medical bills, car repairs, or temporary unemployment.

## Common Planning Guideline

A commonly discussed starting point is three to six months of essential living expenses. The appropriate amount varies with income stability, dependents, insurance, and other circumstances.

## Where to Keep It

Emergency savings are generally held in liquid, relatively low-risk accounts so the money can be accessed when needed.

## Key Takeaway

Emergency funds help reduce the need to borrow or sell investments during unexpected events.
"""
    },
    {
        "id": "basics_010",
        "title": "Investment Risk and Return",
        "category": "investing_basics",
        "source_url": "",
        "content": """# Investment Risk and Return

Investment return describes the gain or loss from an investment over a period. It may include price changes, interest, and dividends.

Risk describes uncertainty about future outcomes, including the possibility of losing money.

## Types of Risk

- Market risk
- Credit risk
- Interest-rate risk
- Inflation risk
- Liquidity risk
- Concentration risk

## Risk Tolerance and Time Horizon

Investors with different financial goals and time horizons may choose different levels of risk.

## Key Takeaway

Higher expected returns often involve greater risk, but taking more risk does not guarantee a higher return.
"""
    },
]

for topic in TOPICS:
    path = OUTPUT_DIR / f"{topic['id']}.md"

    metadata = {
        "article_id": topic["id"],
        "title": topic["title"],
        "category": topic["category"],
        "publisher": "Finnie Educational Content",
        "source_url": topic["source_url"],
        "content_type": "original_summary",
    }

    frontmatter = "\n".join(
        f"{key}: {json.dumps(value)}"
        for key, value in metadata.items()
    )

    path.write_text(
        f"---\n{frontmatter}\n---\n\n{topic['content']}",
        encoding="utf-8",
    )

    print(f"Created: {path}")

print(f"\nGenerated {len(TOPICS)} topic files.")
