"""
QA Chain module integrating Google Gemini with context retrieval and citation generation.
"""

import os
from typing import List, Dict, Any
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except ImportError:
    ChatGoogleGenerativeAI = None

RESEARCH_QA_PROMPT_TEMPLATE = """You are an expert AI Research Assistant specialized in scientific literature analysis, academic peer review, and retrieval-augmented synthesis.

Answer the user's question accurately, strictly grounded in the retrieved research paper excerpts below.

Context:
---------------------
{context}
---------------------

User Question: {question}

Instructions:
1. Provide a comprehensive, clear, and well-structured answer using markdown (bullet points, bold highlights, concise paragraphs).
2. Explicitly cite the document and page number when referring to specific methodologies, figures, equations, or empirical results (e.g. "[Attention Is All You Need, Page 3]").
3. If the context contains relevant technical details, equations, or benchmarks, summarize them accurately.
4. If the retrieved context does not contain enough information to answer the question, state: "The uploaded research paper(s) do not contain sufficient information to answer this question." Do not make up facts or extrapolate beyond the provided text.

Answer:"""


class ResearchPaperQAChain:
    """Orchestrates document context formatting, prompt engineering, and Gemini generation."""

    def __init__(self, api_key: str = None, model_name: str = None, temperature: float = 0.2):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model_name or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
        self.temperature = temperature
        self.llm = self._init_llm()
        self.prompt = PromptTemplate(
            template=RESEARCH_QA_PROMPT_TEMPLATE,
            input_variables=["context", "question"],
        )
        self.output_parser = StrOutputParser()
        self.chain = self.prompt | self.llm | self.output_parser

    def _init_llm(self):
        """Initializes Google Gemini via langchain-google-genai."""
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY is not set. Please provide your Google Gemini API key in the .env file or environment."
            )

        if ChatGoogleGenerativeAI is None:
            raise ImportError(
                "langchain-google-genai is not installed. Please install it via `pip install langchain-google-genai`."
            )

        return ChatGoogleGenerativeAI(
            model=self.model_name,
            google_api_key=self.api_key,
            temperature=self.temperature,
            max_tokens=2048,
        )

    def format_context(self, docs: List[Document]) -> str:
        """Formats retrieved documents into a labeled context block."""
        formatted_chunks = []
        for i, doc in enumerate(docs):
            source = doc.metadata.get("source", "Document")
            page = doc.metadata.get("page", "?")
            header = f"[Excerpt {i+1} | Source: {source} | Page: {page}]"
            content = doc.page_content.strip()
            formatted_chunks.append(f"{header}\n{content}")
        return "\n\n".join(formatted_chunks)

    def extract_sources(self, docs: List[Document]) -> List[Dict[str, Any]]:
        """Extracts unique source citations with snippet previews."""
        sources = []
        seen = set()
        for doc in docs:
            source = doc.metadata.get("source", "Unknown Document")
            page = doc.metadata.get("page", 1)
            key = (source, page)
            
            snippet = doc.page_content.strip().replace("\n", " ")
            if len(snippet) > 220:
                snippet = snippet[:220] + "..."

            if key not in seen:
                seen.add(key)
                sources.append({
                    "document": source,
                    "page": page,
                    "snippet": snippet,
                })
        return sources

    def answer_question(self, question: str, retrieved_docs: List[Document]) -> Dict[str, Any]:
        """
        Executes the QA chain given a question and a list of retrieved document chunks.
        
        Args:
            question: The user's research question.
            retrieved_docs: Chunks retrieved from ChromaDB.
            
        Returns:
            Dictionary containing 'answer', 'sources', and 'chunks_retrieved'.
        """
        if not retrieved_docs:
            return {
                "answer": "No relevant documents or text passages were found to answer this question. Please ensure you have uploaded research paper PDFs.",
                "sources": [],
                "chunks_retrieved": 0,
            }

        context_str = self.format_context(retrieved_docs)
        
        try:
            raw_answer = self.chain.invoke({
                "context": context_str,
                "question": question,
            })
            sources = self.extract_sources(retrieved_docs)
            return {
                "answer": raw_answer.strip(),
                "sources": sources,
                "chunks_retrieved": len(retrieved_docs),
            }
        except Exception as e:
            return {
                "answer": f"An error occurred while generating the answer with Gemini: {str(e)}",
                "sources": self.extract_sources(retrieved_docs),
                "chunks_retrieved": len(retrieved_docs),
                "error": str(e),
            }
