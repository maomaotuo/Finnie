"""Reuse cached embedding weights without checking the Hub on every startup."""
from functools import lru_cache

from huggingface_hub import snapshot_download
from huggingface_hub.errors import LocalEntryNotFoundError
from langchain_huggingface import HuggingFaceEmbeddings

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embeddings():
    # A resolved local snapshot avoids remote metadata requests for cached models.
    # On a new installation the normal model identifier permits the first download.
    try:
        model_path = snapshot_download(MODEL_NAME, local_files_only=True)
    except LocalEntryNotFoundError:
        model_path = MODEL_NAME

    return HuggingFaceEmbeddings(
        model_name=model_path,
        model_kwargs={"device": "cpu", "local_files_only": model_path != MODEL_NAME},
        encode_kwargs={"normalize_embeddings": True},
        show_progress=False,
    )
