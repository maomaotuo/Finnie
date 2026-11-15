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


@pytest.mark.parametrize("model_unavailable", [False, True])
def test_capital_gain_definition_and_followup_go_to_tax(monkeypatch, model_unavailable):
    model = Mock()
    classify = model.with_structured_output.return_value.invoke
    classify.return_value = router.RoutingDecision(agent="finance_qa")
    if model_unavailable:
        classify.side_effect = RuntimeError("Model unavailable")
    monkeypatch.setattr(router, "get_llm", lambda: model)

    first = "What is a long-term capital gain?"
    route = router.workflow_router({"question": first})
    assert route["selected_agent"] == "tax"
    followup = {
        **route,
        "question": "how does is differ from short term gain",
        "history": [{"role": "user", "content": first}],
    }
    assert router.workflow_router(followup)["selected_agent"] == "tax"
    assert router.workflow_router({**followup, "agent_override": "finance_qa"})["selected_agent"] == "finance_qa"
    assert router.workflow_router({**followup, "question": "What is an ETF?"})["selected_agent"] == "finance_qa"
