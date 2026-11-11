"""Goal projections use explicit user assumptions and end-of-month contributions."""
import re
from typing import Literal

from pydantic import BaseModel

from src.core.llm import get_llm
from src.utils.calculators import project_goal
from src.agents.base_agent import DISCLAIMER

class GoalInputs(BaseModel):
    target: float | None = None
    years: float | None = None
    initial: float | None = None
    monthly: float | None = None
    annual_return_pct: float | None = None
    risk_appetite: Literal["conservative", "moderate", "aggressive"] | None = None


def goal_agent(state):
    goal = dict(state.get("goal") or {})
    question = state.get("question", "")
    # Use chat values for this calculation while retaining any saved assumptions
    # the user did not change.
    if question.strip() and (not goal or re.search(r"[0-9]", question)):
        extractor = get_llm().with_structured_output(GoalInputs, method="json_schema")
        inputs = extractor.invoke([
            ("system", "Extract only savings-goal assumptions explicitly supplied by the user. "
             "Return null for missing fields. Amounts are in dollars, timeline is in years "
             "(convert months to years), and annual return is a percentage, so 5% is 5. "
             "Preserve explicit zeros. Do not calculate a projection."),
            ("human", question),
        ])
        goal.update(GoalInputs.model_validate(inputs).model_dump(exclude_none=True))

    fields = {
        "target": "target amount", "years": "timeline", "initial": "current savings",
        "monthly": "monthly contribution", "annual_return_pct": "assumed annual return",
    }
    required = ("target", "years") if state.get("goal") else tuple(fields)
    missing = [fields[field] for field in required if field not in goal]
    if missing:
        return {"answer": "Please provide your " + ", ".join(missing)
                + " in Chat or enter those values in the Goals tab."}
    result = project_goal(**goal)

    def money(amount):
        # Escape dollar signs so Streamlit Markdown displays currency as text.
        return rf"\${amount:,.2f}"

    months = result["trajectory"][-1]["month"]
    duration = (
        f"{months // 12} {'year' if months == 12 else 'years'}"
        if months % 12 == 0
        else f"{months} {'month' if months == 1 else 'months'}"
    )
    status = "You're on track." if result["on_track"] else "You're projected to fall short."
    answer = (
        f"**{status}** At {result['annual_return_pct']:g}% annual return, saving "
        f"{money(result['monthly'])} per month gives you a projected "
        f"**{money(result['projected_value'])}** after {duration}, toward your "
        f"{money(result['target'])} goal."
    )
    if not result["on_track"]:
        extra = result["required_monthly"] - result["monthly"]
        answer += (
            f" The projected shortfall is **{money(result['shortfall'])}**. "
            f"To reach the goal, you'd need about **{money(result['required_monthly'])} "
            f"per month**, or {money(extra)} more than your current contribution."
        )
    else:
        extra = round(result["monthly"] - result["required_monthly"], 2)
        surplus = round(result["projected_value"] - result["target"], 2)
        if extra > 0:
            answer += f" You're contributing **{money(extra)} more per month** than required."
        if surplus > 0:
            answer += f" Your projected balance is **{money(surplus)} above your goal**."
    answer += (
        f"\n\n**Example:** Your projected balance after the first month is "
        f"{money(result['trajectory'][1]['balance'])}."
        f"\n\nThis projection assumes contributions at month end and a constant return. "
        "It excludes taxes, fees, inflation, and volatility. "
        f"Risk appetite is {result['risk_appetite']} and does not change the assumed return."
        f"\n\n{DISCLAIMER}"
    )
    return {"goal_analysis": result, "answer": answer}
