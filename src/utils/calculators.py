"""Validated deterministic financial arithmetic. No LLM performs calculations."""
import math
from collections import defaultdict

def number(value, name, minimum=0, maximum=None):
    if isinstance(value, bool): raise ValueError(f"{name} must be a number")
    try: value = float(value)
    except (TypeError, ValueError): raise ValueError(f"{name} must be a number") from None
    if not math.isfinite(value) or value < minimum or (maximum is not None and value > maximum):
        raise ValueError(f"{name} must be finite and between {minimum} and {maximum if maximum is not None else 'the supported maximum'}")
    return value

def analyze_portfolio(holdings):
    if not holdings: raise ValueError("Portfolio cannot be empty")
    grouped = {}
    for item in holdings:
        symbol = str(item.get("symbol", "")).strip().upper()
        if not symbol: raise ValueError("Each holding needs a symbol")
        asset = str(item.get("asset_type", "")).lower().strip()
        if asset not in {"stock", "etf", "bond", "cash", "mutual_fund", "other"}:
            raise ValueError("Unsupported asset type")
        quantity = number(item.get("quantity"), "Quantity")
        price = number(item.get("price"), "Price")
        if quantity == 0 or price == 0: raise ValueError("Quantity and price must be positive")
        expense = item.get("expense_ratio_pct")
        expense = number(expense, "Expense ratio (%)", 0, 100) if expense is not None else (0 if asset in {"stock", "cash", "bond"} else None)
        if symbol in grouped and grouped[symbol]["asset_type"] != asset:
            raise ValueError("Duplicate symbols must have the same asset type")
        # Combine lots of the same ticker before measuring portfolio weights.
        position = grouped.setdefault(symbol, {"symbol":symbol, "asset_type":asset, "value":0, "annual_fee":0, "fee_known":True})
        value = quantity * price
        if not math.isfinite(value): raise ValueError("Holding value exceeds supported range")
        position["value"] += value
        position["fee_known"] &= expense is not None
        if expense is not None: position["annual_fee"] += value * expense / 100
    total = sum(p["value"] for p in grouped.values())
    if not math.isfinite(total) or total <= 0: raise ValueError("Portfolio value must be positive and finite")
    positions=[]; allocation=defaultdict(float)
    for p in grouped.values():
        weight=p["value"]/total*100
        positions.append({"symbol":p["symbol"], "asset_type":p["asset_type"], "value":round(p["value"],2), "allocation_pct":round(weight,2)})
        allocation[p["asset_type"]] += weight
    # Squaring weights gives larger positions more influence in the concentration measure.
    hhi=sum((p["value"]/total)**2 for p in grouped.values())
    # A missing fund expense ratio makes the total fee estimate unknown.
    fee_known=all(p["fee_known"] for p in grouped.values())
    largest=max(positions,key=lambda p:p["value"])
    return {"total_value":round(total,2), "positions":positions, "largest_position":largest,
            "asset_allocation_pct":{k:round(v,2) for k,v in allocation.items()},
            "direct_stock_allocation_pct":round(allocation.get("stock",0),2),
            "etf_allocation_pct":round(allocation.get("etf",0),2),
            "concentration_score":round(hhi*100,2), "effective_holdings":round(1/hhi,2),
            "risk_label":"Concentrated" if largest["allocation_pct"] > 50 else "Review asset exposure",
            "weighted_expense_ratio_pct":round(sum(p["annual_fee"] for p in grouped.values())/total*100,4) if fee_known else None,
            "estimated_annual_fees":round(sum(p["annual_fee"] for p in grouped.values()),2) if fee_known else None}

def project_goal(target, years, initial=0, monthly=0, annual_return_pct=5, risk_appetite="moderate"):
    target=number(target,"Target",0,1e15)
    if target == 0: raise ValueError("Target must be positive")
    years=number(years,"Years",1/12,100)
    initial=number(initial,"Initial savings",0,1e15)
    monthly=number(monthly,"Monthly contribution",0,1e12)
    rate=number(annual_return_pct,"Annual return (%)",-50,50)
    if risk_appetite not in {"conservative","moderate","aggressive"}: raise ValueError("Invalid risk appetite")
    months=round(years*12)
    # Convert the effective annual return to its equivalent compounded monthly rate.
    r=(1+rate/100)**(1/12)-1
    factor=(1+r)**months
    # At zero return, each contribution simply adds its face value.
    annuity=months if abs(r)<1e-12 else (factor-1)/r
    # Subtract the future value of existing savings, then solve for the monthly deposit.
    required=max(0,(target-initial*factor)/annuity)
    balance=initial; trajectory=[{"month":0,"balance":round(balance,2),"contributions":round(initial,2)}]
    for month in range(1,months+1):
        # Apply one month of growth before adding the end-of-month contribution.
        balance=balance*(1+r)+monthly
        trajectory.append({"month":month,"balance":round(balance,2),"contributions":round(initial+monthly*month,2)})
    return {"target":target,"years":months/12,"initial":initial,"monthly":monthly,
            "annual_return_pct":rate,"risk_appetite":risk_appetite,
            "projected_value":round(balance,2),"required_monthly":round(required,2),
            "shortfall":round(max(0,target-balance),2),"on_track":balance+0.005>=target,
            "trajectory":trajectory}
