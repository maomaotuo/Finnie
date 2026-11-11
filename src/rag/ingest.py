
"""Load, filter, chunk, and index local knowledge-base documents."""

import json
from pathlib import Path

import frontmatter
from langchain_core.documents import Document
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.rag.embeddings import get_embeddings


from src.core.config import ROOT, option

KNOWLEDGE_BASE_PATH = ROOT / "src/data/knowledge_base"
ARTICLE_DIR = KNOWLEDGE_BASE_PATH / "articles"
MANIFEST_PATH = ROOT / "src/data/article_sources.json"
VECTORSTORE_PATH = ROOT / "src/rag/faiss_index"

ALLOWED_REVIEW_STATUSES = {"candidate"}


def load_json_articles():
    """Load only curated article candidates."""

    data = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    sources = data if isinstance(data, list) else data["articles"]

    # Use the manifest to decide which downloaded articles are eligible for indexing.
    eligible_sources = {
        source["id"]: source
        for source in sources
        if source.get("review_status") in ALLOWED_REVIEW_STATUSES
    }

    print(f"Eligible articles in manifest: {len(eligible_sources)}")

    documents = []

    for path in sorted(ARTICLE_DIR.glob("*.json")):
        article = json.loads(path.read_text(encoding="utf-8"))
        article_id = article["id"]

        if article_id not in eligible_sources:
            continue

        if article.get("content_type") == "resource_directory":
            continue

        content = article.get("content", "").strip()

        if len(content) < 1000:
            print(f"Skipping short article: {article_id}")
            continue

        source = eligible_sources[article_id]

        documents.append(
            Document(
                page_content=content,
                metadata={
                    "article_id": article_id,
                    "title": source["title"],
                    "category": source["category"],
                    "publisher": source["publisher"],
                    "source_url": source["url"],
                    "retrieved_at": article.get("retrieved_at") or "",
                    "review_status": source["review_status"],
                },
            )
        )

    return documents


def load_markdown_documents():
    """Load Markdown files with YAML frontmatter."""

    documents = []

    for path in sorted(KNOWLEDGE_BASE_PATH.rglob("*.md")):
        # Frontmatter separates article metadata from the Markdown body that gets embedded.
        post = frontmatter.load(str(path))

        documents.append(
            Document(
                page_content=post.content,
                metadata={
                    "article_id": str(post.get("article_id", "")),
                    "title": str(post.get("title", path.stem)),
                    "category": str(post.get("category", "")),
                    "publisher": str(post.get("publisher", "")),
                    "source_url": str(post.get("source_url", "")),
                    "content_type": str(
                        post.get("content_type", "original_summary")
                    ),
                    "source": str(path),
                },
            )
        )

    return documents


def build_vectorstore():
    """Rebuild the FAISS index using local embeddings."""

    markdown_documents = load_markdown_documents()
    article_documents = load_json_articles()

    documents = markdown_documents + article_documents

    if not documents:
        raise ValueError("No knowledge-base documents found")

    print(f"Loaded {len(markdown_documents)} Markdown documents")
    print(f"Loaded {len(article_documents)} curated articles")
    print(f"Total documents: {len(documents)}")

    # Smaller passages make retrieval more precise. Chunks retain their source metadata.
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=int(option("chunk_size", 500)),
        chunk_overlap=int(option("chunk_overlap", 100)),
    )

    chunks = splitter.split_documents(documents)

    print(f"Created {len(chunks)} chunks")

    embeddings = get_embeddings()

    BATCH_SIZE = 20
    vectorstore = None

    for start in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[start:start + BATCH_SIZE]

        print(
            f"Embedding chunks {start + 1}–"
            f"{start + len(batch)} of {len(chunks)}"
        )

        # The first batch creates a fresh index. Later batches add to that same index.
        if vectorstore is None:
            vectorstore = FAISS.from_documents(
                batch,
                embeddings,
            )
        else:
            vectorstore.add_documents(batch)

    if vectorstore is None:
        raise ValueError("No chunks available for indexing")

    # Save only after the complete index has been built.
    VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
    vectorstore.save_local(str(VECTORSTORE_PATH))

    print(f"\nFAISS index saved to {VECTORSTORE_PATH}")
    print(f"Total vectors: {vectorstore.index.ntotal}")


if __name__ == "__main__":
    build_vectorstore()
