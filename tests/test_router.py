from unittest.mock import Mock
import pytest
import src.workflow.router as router
@pytest.mark.parametrize('question,agent', [('What is an ETF?','finance_qa'),('Analyze my holdings','portfolio'),('AAPL price today','market'),('Save for a house','goal'),('Latest headlines','news'),('Capital gains tax','tax')])
def test_fallback_routes(question,agent,monkeypatch):
    monkeypatch.setattr(router,'get_llm',Mock(side_effect=RuntimeError))
    assert router.workflow_router({'question':question})['selected_agent']==agent

def test_override_never_calls_llm(monkeypatch):
    llm=Mock();monkeypatch.setattr(router,'get_llm',llm)
    r=router.workflow_router({'question':'anything','agent_override':'goal','sources':[{'title':'stale'}]})
    assert r['selected_agent']=='goal'
    assert r['sources']==[]
    llm.assert_not_called()

def test_llm_route(monkeypatch):
    model=Mock();model.with_structured_output.return_value.invoke.return_value=router.RoutingDecision(agent='portfolio')
    monkeypatch.setattr(router,'get_llm',lambda:model)
    assert router.workflow_router({'question':'Review this'})['selected_agent']=='portfolio'

def test_followup():
    assert router.fallback_route('What about that instead?','goal')=='goal'
