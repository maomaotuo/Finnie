from unittest.mock import Mock
from langchain_core.documents import Document
import src.agents.finance_qa_agent as qa
import src.rag.pipeline as rag
import src.agents.tax_agent as tax
from src.agents.base_agent import DISCLAIMER


def test_tax_query_is_not_polluted_by_generation_policy_or_old_refusal(monkeypatch):
    retriever = Mock()
    retriever.invoke.return_value = [Document(
        page_content='Assets held more than one year generally produce long-term gains.',
        metadata={'title': 'IRS capital gains', 'source_url': 'https://www.irs.gov/taxtopics/tc409'},
    )]
    model = Mock()
    model.invoke.return_value = Mock(text='For U.S. federal taxes, more than one year generally means long-term [1].')
    monkeypatch.setattr(rag, 'get_retriever', lambda category, **kwargs: retriever)
    monkeypatch.setattr(rag, 'get_llm', lambda: model)
    question = 'What is long term capital gain?'
    result = tax.tax_agent({'question': question, 'history': [
        {'role': 'user', 'content': 'What are capital gains?'},
        {'role': 'assistant', 'content': 'Not enough information. Tax thresholds depend on jurisdiction.'},
    ]})
    retriever.invoke.assert_called_once_with(question)
    prompt = model.invoke.call_args.args[0][0][1]
    assert 'absence of current-year brackets' in prompt
    assert len(result['sources']) == 1
    assert result['answer'].count(DISCLAIMER) == 1


def test_followup_search_uses_prior_user_topic_not_prior_model_answer(monkeypatch):
    retriever = Mock(invoke=Mock(return_value=[]))
    monkeypatch.setattr(rag, 'get_retriever', lambda category, **kwargs: retriever)
    qa.finance_qa_agent({'question': 'How does it differ from a short-term gain?', 'history': [
        {'role': 'user', 'content': 'What is a long-term capital gain?'},
        {'role': 'assistant', 'content': 'Previous irrelevant refusal about thresholds'},
    ]})
    query = retriever.invoke.call_args.args[0]
    assert 'long-term capital gain' in query
    assert 'Previous irrelevant refusal' not in query


def test_tax_footer_is_not_duplicated(monkeypatch):
    monkeypatch.setattr(tax, 'answer_with_rag', lambda *args, **kwargs: {
        'answer': 'Explanation [1].\n\n' + (tax.TAX_NOTE + ' ' + DISCLAIMER + '\n\n') * 2,
        'sources': [],
    })
    answer = tax.tax_agent({'question': 'Capital gains?'})['answer']
    assert answer.count(tax.TAX_NOTE) == 1
    assert answer.count(DISCLAIMER) == 1
