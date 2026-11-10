"""
RAG (Retrieval-Augmented Generation) package for AI Research Paper Assistant.
"""

from rag.pdf_loader import extract_text_from_pdf
from rag.chunking import split_documents_into_chunks
from rag.embeddings import get_embedding_model
from rag.vector_store import VectorStoreManager
from rag.qa_chain import ResearchPaperQAChain

__all__ = [
    "extract_text_from_pdf",
    "split_documents_into_chunks",
    "get_embedding_model",
    "VectorStoreManager",
    "ResearchPaperQAChain",
]
