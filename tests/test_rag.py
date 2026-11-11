from unittest.mock import Mock
from langchain_core.documents import Document
from src.rag.pipeline import build_context
import src.rag.retriever as retrieval
from src.rag.ingest import load_json_articles, load_markdown_documents

def test_curated_knowledge_base():
    articles=load_json_articles()
    assert 50<=len(articles)<=100
    assert all(d.metadata['source_url'].startswith('https://') for d in articles)
    assert all(d.metadata['review_status']=='candidate' for d in articles)
    assert len(load_markdown_documents())>=10

def test_category_filter(monkeypatch):
    retrieval.get_retriever.cache_clear()
    retrieval.get_vectorstore.cache_clear()
    store=Mock()
    monkeypatch.setattr(retrieval,'get_embeddings',lambda:Mock())
    monkeypatch.setattr(retrieval.FAISS,'load_local',Mock(return_value=store))
    monkeypatch.setenv("RETRIEVAL_MAX_DISTANCE", "0.8")
    original = Document(page_content="A passage", metadata={"article_id": "a"})
    store.similarity_search_with_score.return_value = [(original, 0.8), (original, 0.4), (original, 0.81)]
    documents = retrieval.get_retriever("stocks").invoke("What are stocks?")
    assert store.similarity_search_with_score.call_args.kwargs["filter"] == {"category": "stocks"}
    assert [doc.metadata["faiss_distance"] for doc in documents] == [0.8, 0.4]
    assert "faiss_distance" not in original.metadata
    _, sources = build_context(documents)
    assert len(sources) == 1
    assert sources[0]["faiss_distance"] == 0.4
    retrieval.get_retriever.cache_clear()
    retrieval.get_vectorstore.cache_clear()
