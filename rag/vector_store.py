"""
Vector store manager wrapping ChromaDB for persistent document indexing and semantic retrieval.
"""

import os
import shutil
from typing import List, Dict, Any, Tuple
from langchain_core.documents import Document

try:
    from langchain_chroma import Chroma
except ImportError:
    from langchain_community.vectorstores import Chroma

from rag.embeddings import get_embedding_model


class VectorStoreManager:
    """Manages persistent ChromaDB vector storage and semantic search operations."""

    def __init__(self, persist_directory: str = "data/chroma_db", collection_name: str = "research_papers"):
        self.persist_directory = os.path.abspath(persist_directory)
        self.collection_name = collection_name
        os.makedirs(self.persist_directory, exist_ok=True)
        self.embedding_function = get_embedding_model()
        self._vector_store = None
        self._init_vector_store()

    def _init_vector_store(self):
        """Initializes the Chroma persistent client."""
        self._vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embedding_function,
            persist_directory=self.persist_directory,
        )

    def add_documents(self, documents: List[Document]) -> int:
        """
        Adds chunked documents into the ChromaDB collection.
        
        Args:
            documents: List of chunked Document objects.
            
        Returns:
            Number of documents added.
        """
        if not documents:
            return 0

        self._vector_store.add_documents(documents)
        return len(documents)

    def similarity_search(self, query: str, k: int = 4) -> List[Document]:
        """
        Searches for the k most semantically similar chunks for a given query.
        
        Args:
            query: Question or search string.
            k: Number of relevant chunks to retrieve.
            
        Returns:
            List of matching Document objects.
        """
        if not self._vector_store:
            return []
        return self._vector_store.similarity_search(query, k=k)

    def similarity_search_with_score(
        self, query: str, k: int = 4
    ) -> List[Tuple[Document, float]]:
        """
        Retrieves matching chunks along with similarity distance score.
        """
        if not self._vector_store:
            return []
        return self._vector_store.similarity_search_with_score(query, k=k)

    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """
        Inspects the collection and returns a summary of indexed documents.
        
        Returns:
            List of dicts with 'filename', 'chunks_count', and 'pages_covered'.
        """
        try:
            collection = self._vector_store._collection
            metadata_items = collection.get().get("metadatas", [])
            
            summary: Dict[str, Dict[str, Any]] = {}
            for meta in metadata_items:
                if not meta:
                    continue
                source = meta.get("source", "Unknown Document")
                page = meta.get("page", 1)
                
                if source not in summary:
                    summary[source] = {
                        "filename": source,
                        "chunk_count": 0,
                        "pages": set(),
                    }
                summary[source]["chunk_count"] += 1
                summary[source]["pages"].add(page)

            result = []
            for item in summary.values():
                result.append({
                    "filename": item["filename"],
                    "chunk_count": item["chunk_count"],
                    "total_pages": len(item["pages"]),
                })
            return result
        except Exception as e:
            print(f"[Warning] Error getting indexed files: {e}")
            return []

    def get_total_chunks(self) -> int:
        """Returns the total number of chunks indexed in ChromaDB."""
        try:
            return self._vector_store._collection.count()
        except Exception:
            return 0

    def clear(self) -> bool:
        """
        Clears all indexed documents from the collection and reinitializes.
        """
        try:
            # Delete collection
            self._vector_store.delete_collection()
        except Exception:
            pass

        try:
            # Clean directory if needed
            if os.path.exists(self.persist_directory):
                shutil.rmtree(self.persist_directory, ignore_errors=True)
            os.makedirs(self.persist_directory, exist_ok=True)
        except Exception as e:
            print(f"[Warning] Could not wipe directory completely: {e}")

        # Re-initialize vector store
        self._init_vector_store()
        return True

    def as_retriever(self, search_kwargs: Dict[str, Any] = None):
        """Returns a LangChain retriever interface for the vector store."""
        kwargs = search_kwargs or {"k": 4}
        return self._vector_store.as_retriever(search_kwargs=kwargs)
