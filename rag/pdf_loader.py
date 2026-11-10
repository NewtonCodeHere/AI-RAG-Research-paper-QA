"""
PDF Loader module for extracting text and metadata from research paper PDFs using PyPDF2 / pypdf.
"""

import os
from typing import List, Dict, Any
from langchain_core.documents import Document

try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import pypdf
except ImportError:
    pypdf = None


def clean_text(text: str) -> str:
    """Clean extracted text from PDF by removing null bytes and normalizing whitespace."""
    if not text:
        return ""
    # Remove null characters
    text = text.replace("\x00", "")
    # Normalize multiple newlines/spaces
    lines = [line.strip() for line in text.splitlines()]
    cleaned = "\n".join(line for line in lines if line)
    return cleaned


def extract_text_from_pdf(file_path: str, original_filename: str = None) -> List[Document]:
    """
    Extracts text page-by-page from a PDF file using PyPDF2 or pypdf.
    
    Args:
        file_path: Absolute or relative path to the PDF file.
        original_filename: Optional display name for the document.
        
    Returns:
        List of LangChain Document objects with page content and metadata.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"PDF file not found at path: {file_path}")

    filename = original_filename or os.path.basename(file_path)
    documents: List[Document] = []

    # Choose reader: PyPDF2 or pypdf
    pdf_reader = None
    file_handle = open(file_path, "rb")

    try:
        if PyPDF2 is not None:
            pdf_reader = PyPDF2.PdfReader(file_handle)
        elif pypdf is not None:
            pdf_reader = pypdf.PdfReader(file_handle)
        else:
            raise ImportError("Neither PyPDF2 nor pypdf is installed.")

        total_pages = len(pdf_reader.pages)

        for page_idx, page in enumerate(pdf_reader.pages):
            try:
                page_text = page.extract_text() or ""
                cleaned = clean_text(page_text)
                
                if cleaned:
                    metadata: Dict[str, Any] = {
                        "source": filename,
                        "file_path": file_path,
                        "page": page_idx + 1,
                        "total_pages": total_pages,
                    }
                    doc = Document(page_content=cleaned, metadata=metadata)
                    documents.append(doc)
            except Exception as page_err:
                # Log page extraction issue and continue with remaining pages
                print(f"[Warning] Error extracting page {page_idx + 1} of {filename}: {page_err}")
                continue

    finally:
        file_handle.close()

    return documents
