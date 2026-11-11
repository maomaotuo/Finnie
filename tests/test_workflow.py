from unittest.mock import Mock
import src.workflow.graph as workflow

def test_memory_session_isolation_and_reset(monkeypatch):
    monkeypatch.setattr(workflow,'finance_qa_agent',lambda state:dict(answer='ETF [1]',sources=[dict(title='ETF')]))
    app=workflow.build_graph()
    a={'configurable':{'thread_id':'a'}};b={'configurable':{'thread_id':'b'}}
    first=app.invoke({'question':'ETF?','agent_override':'finance_qa'},a)
    assert len(first['history'])==2
    second=app.invoke({'question':'My goal','agent_override':'goal'},a)
    assert len(second['history'])==4
    assert second['sources']==[]
    isolated=app.invoke({'question':'Goal','agent_override':'goal'},b)
    assert len(isolated['history'])==2
    assert 'ETF?' not in str(isolated['history'])

def test_guarded_failures():
    def bad(_): raise RuntimeError('secret error')
    def invalid(_): raise ValueError('bad holdings')
    assert workflow.guarded(bad)({})['error']=='service_unavailable'
    assert 'secret' not in workflow.guarded(bad)({})['answer']
    assert workflow.guarded(invalid)({})['error']=='validation'

def test_history_bounded():
    state=dict(history=[dict(role='user',content='old')]*20,question='new',answer='new')
    assert len(workflow.remember(state)['history'])==20


def test_greeting_bypasses_specialists_and_preserves_next_question(monkeypatch):
    import src.workflow.router as router

    model = Mock(side_effect=AssertionError("Greeting should not call the router model"))
    monkeypatch.setattr(router, "get_llm", model)
    specialist = Mock(return_value={"answer": "An ETF is a fund."})
    monkeypatch.setattr(workflow, "finance_qa_agent", specialist)
    graph = workflow.build_graph()
    config = {"configurable": {"thread_id": "greeting"}}
    greeting = graph.invoke({"question": "Hi, Finnie!", "agent_override": "tax"}, config)
    assert greeting["answer"].startswith("Hi! I’m Finnie.")
    assert greeting["sources"] == []
    model.assert_not_called()
    specialist.assert_not_called()

    reply = graph.invoke({"question": "Hi, what is an ETF?", "agent_override": "finance_qa"}, config)
    assert reply["answer"] == "An ETF is a fund."
    assert not reply["is_greeting"]
    assert len(reply["history"]) == 4
