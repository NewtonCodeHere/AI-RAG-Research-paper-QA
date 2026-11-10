"""
Embeddings module providing Hugging Face Sentence Transformers embeddings.
"""

import os
from typing import Optional

_embedding_instance = None


def get_embedding_model(model_name: Optional[str] = None):
    """
    Returns a cached instance of HuggingFaceEmbeddings using Sentence Transformers.
    
    Args:
        model_name: Name of the Hugging Face sentence-transformers model.
                    Defaults to EMBEDDING_MODEL_NAME env var or 'sentence-transformers/all-MiniLM-L6-v2'.
                    
    Returns:
        HuggingFaceEmbeddings instance compatible with LangChain and ChromaDB.
    """
    global _embedding_instance

    if _embedding_instance is not None and model_name is None:
        return _embedding_instance

    target_model = model_name or os.getenv(
        "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
    )

    try:
        # Prefer new langchain_huggingface if installed
        from langchain_huggingface import HuggingFaceEmbeddings
    except ImportError:
        try:
            # Fallback to langchain_community
            from langchain_community.embeddings import HuggingFaceEmbeddings
        except ImportError:
            raise ImportError(
                "Neither langchain_huggingface nor langchain_community.embeddings is available. "
                "Please run `pip install sentence-transformers langchain-huggingface`."
            )

    model_kwargs = {"device": "cpu"}
    encode_kwargs = {"normalize_embeddings": True}

    embeddings = HuggingFaceEmbeddings(
        model_name=target_model,
        model_kwargs=model_kwargs,
        encode_kwargs=encode_kwargs,
    )

    if model_name is None:
        _embedding_instance = embeddings

    return embeddings
