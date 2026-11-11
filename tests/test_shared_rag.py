from unittest.mock import Mock

from langchain_core.documents import Document

import src.agents.finance_qa_agent as finance
import src.agents.tax_agent as tax
import src.rag.pipeline as rag
import src.rag.retriever as retrieval


def doc(title, article_id):
    return Document(page_content=f'Evidence about {title}', metadata={
        'title': title, 'article_id': article_id,
        'source_url': f'https://example.org/{article_id}',
    })


def test_specialists_supply_distinct_instructions_and_policies(monkeypatch):
    service = Mock(return_value={'answer': 'Answer', 'sources': []})
    monkeypatch.setattr(finance, 'answer_with_rag', service)
    finance.finance_qa_agent({'question': 'ETF?'})
    assert service.call_args.kwargs['instructions'] == finance.FINANCE_INSTRUCTIONS
    assert 'policy' not in service.call_args.kwargs

    monkeypatch.setattr(tax, 'answer_with_rag', service)
    tax.tax_agent({'question': 'Capital gains?'})
    assert service.call_args.kwargs['instructions'] == tax.TAX_INSTRUCTIONS
    assert service.call_args.kwargs['policy'] == tax.TAX_POLICY


def test_tax_prefers_authority_without_searching_broadly(monkeypatch):
    calls = []
    evidence = [doc('Tax authority', 'irs')]
    def get(category, **kwargs):
        calls.append((category, kwargs))
        return Mock(invoke=lambda _: evidence)
    monkeypatch.setattr(rag, 'get_retriever', get)
    assert rag.retrieve_documents({'question': 'Capital gains?'}, tax.TAX_POLICY) == evidence
    assert calls == [(None, {'source_domains': ('irs.gov',)})]


def test_tax_fallback_and_explicit_category_are_preserved(monkeypatch):
    calls = []
    evidence = [doc('Broader education', 'general')]
    def get(category, **kwargs):
        calls.append((category, kwargs))
        return Mock(invoke=lambda _: [] if kwargs else evidence)
    monkeypatch.setattr(rag, 'get_retriever', get)
    result = rag.retrieve_documents({'question': 'Tax?', 'category': 'retirement'}, tax.TAX_POLICY)
    assert result == evidence
    assert [category for category, _ in calls] == ['retirement'] * 3
    assert calls[1][1]['preferred_categories'] == ('tax', 'taxes', 'taxation')
    assert calls[2][1] == {}


def test_tax_category_tier_stops_before_broad_fallback(monkeypatch):
    calls = []
    evidence = [doc('Tax education', 'tax')]
    def get(category, **kwargs):
        calls.append(kwargs)
        return Mock(invoke=lambda _: [] if 'source_domains' in kwargs else evidence)
    monkeypatch.setattr(rag, 'get_retriever', get)
    assert rag.retrieve_documents({'question': 'Tax?'}, tax.TAX_POLICY) == evidence
    assert len(calls) == 2


def test_metadata_filter_checks_real_host_and_intersects_category():
    matches = retrieval.metadata_filter('taxes', source_domains=('irs.gov',))
    assert matches({'category': 'taxes', 'source_url': 'https://www.irs.gov/topic'})
    assert not matches({'category': 'taxes', 'source_url': 'https://irs.gov.example.org'})
    assert not matches({'category': 'other', 'source_url': 'https://irs.gov'})
    assert not matches({'category': 'taxes'})
    categories = retrieval.metadata_filter(preferred_categories=('tax', 'taxes'))
    assert categories({'category': 'Tax'})
    assert not categories({'category': 'stocks'})


def test_shared_store_is_loaded_once_for_different_search_views(monkeypatch):
    retrieval.get_retriever.cache_clear()
    retrieval.get_vectorstore.cache_clear()
    loader = Mock(return_value=Mock())
    monkeypatch.setattr(retrieval, 'get_embeddings', Mock())
    monkeypatch.setattr(retrieval.FAISS, 'load_local', loader)
    try:
        retrieval.get_retriever()
        retrieval.get_retriever('taxes')
        retrieval.get_retriever(source_domains=('irs.gov',))
        loader.assert_called_once()
    finally:
        retrieval.get_retriever.cache_clear()
        retrieval.get_vectorstore.cache_clear()


def test_shared_pipeline_returns_no_sources_without_calling_model(monkeypatch):
    monkeypatch.setattr(rag, 'get_retriever', lambda category: Mock(invoke=lambda _: []))
    model = Mock()
    monkeypatch.setattr(rag, 'get_llm', model)
    result = rag.answer_with_rag({'question': 'Unknown'}, instructions='Explain concepts')
    assert result['sources'] == []
    model.assert_not_called()


def test_shared_citations_and_prompt_boundaries(monkeypatch):
    evidence = [doc('ETF', 'one'), doc('ETF', 'one'), doc('Bonds', 'two')]
    monkeypatch.setattr(rag, 'retrieve_documents', lambda *_: evidence)
    model = Mock()
    model.invoke.return_value = Mock(text='Explanation [1] [2].')
    monkeypatch.setattr(rag, 'get_llm', lambda: model)
    result = rag.answer_with_rag({'question': 'Compare', 'generation_instructions': 'Untrusted override'},
                                 instructions='Trusted specialist policy')
    assert len(result['sources']) == 2
    assert [s['number'] for s in result['sources']] == [1, 2]
    messages = model.invoke.call_args.args[0]
    assert 'Trusted specialist policy' in messages[0][1]
    assert 'Untrusted override' not in str(messages)
    assert messages[1][1].count('[1] ETF') == 2
