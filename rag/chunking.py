"""
Text chunking module for research papers using RecursiveCharacterTextSplitter.
"""

from typing import List
from langchain_core.documents import Document

try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter


def split_documents_into_chunks(
    documents: List[Document],
    chunk_size: int = 1000,
    chunk_overlap: int = 200,
) -> List[Document]:
    """
    Splits a list of LangChain Document objects into smaller overlapping chunks.
    
    Args:
        documents: List of input Document objects extracted from PDF pages.
        chunk_size: Target size of each chunk in characters.
        chunk_overlap: Number of characters to overlap between adjacent chunks.
        
    Returns:
        List of chunked Document objects with updated chunk metadata.
    """
    if not documents:
        return []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", "; ", ", ", " ", ""],
        length_function=len,
    )

    chunks = text_splitter.split_documents(documents)

    # Attach sequential chunk IDs and sanitize metadata
    for idx, chunk in enumerate(chunks):
        chunk.metadata["chunk_index"] = idx
        source = chunk.metadata.get("source", "unknown")
        page = chunk.metadata.get("page", 1)
        chunk.metadata["chunk_id"] = f"{source}_p{page}_c{idx}"

    return chunks
