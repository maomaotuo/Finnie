import math
import pytest
from src.utils.calculators import analyze_portfolio, project_goal, number

HOLDINGS=[dict(symbol='A',quantity=1,price=100,asset_type='stock'),dict(symbol='B',quantity=1,price=100,asset_type='etf',expense_ratio_pct=0.1)]
def test_portfolio_metrics():
    r=analyze_portfolio(HOLDINGS)
    assert r['total_value']==200
    assert r['direct_stock_allocation_pct']==50
    assert r['etf_allocation_pct']==50
    assert r['effective_holdings']==2
    assert r['concentration_score']==50
    assert r['weighted_expense_ratio_pct']==0.05
    assert r['estimated_annual_fees']==0.1

def test_duplicate_holdings_aggregate():
    r=analyze_portfolio([HOLDINGS[0],HOLDINGS[0]])
    assert len(r['positions'])==1
    assert r['largest_position']['allocation_pct']==100
    assert r['risk_label']=='Concentrated'

def test_unknown_fund_fee():
    assert analyze_portfolio([dict(symbol='F',quantity=1,price=10,asset_type='etf')])['estimated_annual_fees'] is None

@pytest.mark.parametrize('field,value',[('quantity',-1),('quantity',0),('quantity',float('nan')),('price',float('inf')),('price',0),('asset_type','invalid'),('symbol',''),('expense_ratio_pct',101)])
def test_invalid_holdings(field,value):
    with pytest.raises(ValueError): analyze_portfolio([{**HOLDINGS[0],field:value}])

def test_empty_and_conflicting():
    with pytest.raises(ValueError): analyze_portfolio([])
    with pytest.raises(ValueError): analyze_portfolio([HOLDINGS[0],{**HOLDINGS[0],'asset_type':'etf'}])

@pytest.mark.parametrize('value',[True,None,'bad',float('inf'),-1])
def test_invalid_number(value):
    with pytest.raises(ValueError): number(value,'Test')

def test_zero_return_goal():
    r=project_goal(12000,1,monthly=1000,annual_return_pct=0)
    assert r['required_monthly']==1000
    assert r['projected_value']==12000
    assert r['on_track']
    assert len(r['trajectory'])==13

def test_compounding_and_already_funded():
    r=project_goal(1100,1,initial=1000,annual_return_pct=10)
    assert r['projected_value']==1100
    assert r['required_monthly']==0
    assert project_goal(1000,1,initial=2000,annual_return_pct=-10)['required_monthly']==0
    assert project_goal(10000,10,monthly=10)['shortfall']>0

@pytest.mark.parametrize('args',[dict(target=0,years=1),dict(target=10,years=0),dict(target=10,years=1,risk_appetite='unknown'),dict(target=10,years=1,annual_return_pct=-100)])
def test_invalid_goal(args):
    with pytest.raises(ValueError): project_goal(**args)
