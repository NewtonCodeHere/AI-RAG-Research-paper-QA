"""
AI Research Paper Assistant using RAG - Main Flask Application.
Author: Mani Barathi P (NewtonCode)
Organization: CodeBind Technologies
"""

import os
import glob
from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

from rag.pdf_loader import extract_text_from_pdf
from rag.chunking import split_documents_into_chunks
from rag.vector_store import VectorStoreManager
from rag.qa_chain import ResearchPaperQAChain
from utils.helpers import (
    allowed_file,
    sanitize_filename,
    format_file_size,
    get_current_timestamp,
    validate_environment,
)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "rag-research-paper-secret-key-2026")
CORS(app)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "uploads")
DATA_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "chroma_db")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 64 * 1024 * 1024  # 64 MB max upload

# Initialize Vector Store Manager
vector_store_manager = VectorStoreManager(persist_directory=DATA_FOLDER)


def get_qa_chain() -> ResearchPaperQAChain:
    """Helper to instantiate QA Chain with current environment credentials."""
    api_key = os.getenv("GEMINI_API_KEY")
    model_name = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    return ResearchPaperQAChain(api_key=api_key, model_name=model_name)


@app.route("/")
def index():
    """Renders the primary web interface."""
    return render_template("index.html")


@app.route("/api/health", methods=["GET"])
def health_check():
    """Returns application status, API configuration status, and indexed chunk count."""
    env_valid, env_message = validate_environment()
    total_chunks = vector_store_manager.get_total_chunks()
    indexed_docs = vector_store_manager.get_indexed_files()

    return jsonify({
        "status": "online",
        "gemini_api_configured": env_valid,
        "gemini_model": os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        "total_chunks": total_chunks,
        "indexed_documents_count": len(indexed_docs),
        "message": env_message,
    })


@app.route("/api/documents", methods=["GET"])
def get_documents():
    """Returns the list of currently indexed research papers with chunk details."""
    docs = vector_store_manager.get_indexed_files()
    total_chunks = vector_store_manager.get_total_chunks()
    return jsonify({
        "success": True,
        "documents": docs,
        "total_chunks": total_chunks,
    })


@app.route("/api/upload", methods=["POST"])
def upload_files():
    """
    Handles PDF uploads, text extraction, recursive chunking, and embedding into ChromaDB.
    Supports single or multiple file uploads under 'files' or 'files[]'.
    """
    uploaded_files = request.files.getlist("files") or request.files.getlist("files[]")

    if not uploaded_files or (len(uploaded_files) == 1 and uploaded_files[0].filename == ""):
        return jsonify({"success": False, "error": "No files selected for upload."}), 400

    processed_summary = []
    total_new_chunks = 0
    all_chunks_to_add = []

    for file in uploaded_files:
        if not file or not file.filename:
            continue

        if not allowed_file(file.filename):
            return jsonify({
                "success": False,
                "error": f"Invalid file type for '{file.filename}'. Only PDF files are supported.",
            }), 400

        clean_name = sanitize_filename(file.filename)
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], clean_name)
        file.save(save_path)
        file_size = os.path.getsize(save_path)

        try:
            # 1. Extract text and pages with PyPDF2
            extracted_docs = extract_text_from_pdf(save_path, original_filename=clean_name)
            
            if not extracted_docs:
                processed_summary.append({
                    "filename": clean_name,
                    "status": "warning",
                    "message": "No extractable text found (document may be scanned images).",
                    "chunks": 0,
                    "pages": 0,
                    "size": format_file_size(file_size),
                })
                continue

            # 2. Split into overlapping chunks
            chunks = split_documents_into_chunks(extracted_docs, chunk_size=1000, chunk_overlap=200)
            all_chunks_to_add.extend(chunks)
            total_new_chunks += len(chunks)

            processed_summary.append({
                "filename": clean_name,
                "status": "success",
                "chunks": len(chunks),
                "pages": len(extracted_docs),
                "size": format_file_size(file_size),
            })
        except Exception as e:
            processed_summary.append({
                "filename": clean_name,
                "status": "error",
                "error": str(e),
                "chunks": 0,
            })

    # 3. Store into ChromaDB
    if all_chunks_to_add:
        vector_store_manager.add_documents(all_chunks_to_add)

    return jsonify({
        "success": True,
        "message": f"Successfully processed {len(processed_summary)} document(s) with {total_new_chunks} text chunks indexed.",
        "results": processed_summary,
        "total_chunks_indexed": vector_store_manager.get_total_chunks(),
    })


@app.route("/api/query", methods=["POST"])
def query_knowledge_base():
    """
    Receives user query, retrieves top-k relevant chunks from ChromaDB,
    and generates grounded response using Google Gemini with page citations.
    """
    data = request.get_json() or {}
    question = data.get("question", "").strip()
    top_k = int(data.get("k", 4))

    if not question:
        return jsonify({"success": False, "error": "Question parameter is required."}), 400

    # Check if vector store has any indexed data
    total_chunks = vector_store_manager.get_total_chunks()
    if total_chunks == 0:
        return jsonify({
            "success": True,
            "answer": "No research papers have been uploaded or indexed yet. Please upload one or more PDF papers first using the upload panel on the left.",
            "sources": [],
            "timestamp": get_current_timestamp(),
        })

    # Validate Gemini API Key
    env_valid, env_message = validate_environment()
    if not env_valid:
        return jsonify({
            "success": False,
            "error": "Google Gemini API key is missing. Please set GEMINI_API_KEY in your .env file.",
        }), 400

    try:
        # 1. Semantic search in ChromaDB
        relevant_docs = vector_store_manager.similarity_search(question, k=top_k)

        # 2. Invoke Gemini QA Chain
        qa_chain = get_qa_chain()
        result = qa_chain.answer_question(question=question, retrieved_docs=relevant_docs)

        return jsonify({
            "success": True,
            "question": question,
            "answer": result.get("answer"),
            "sources": result.get("sources", []),
            "chunks_retrieved": result.get("chunks_retrieved", 0),
            "timestamp": get_current_timestamp(),
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Failed to generate answer: {str(e)}",
            "timestamp": get_current_timestamp(),
        }), 500


@app.route("/api/clear", methods=["POST"])
def clear_knowledge_base():
    """Clears all indexed chunks from ChromaDB and purges uploaded files."""
    try:
        vector_store_manager.clear()

        # Clean upload folder files (keep .gitkeep)
        for f in glob.glob(os.path.join(app.config["UPLOAD_FOLDER"], "*")):
            if not f.endswith(".gitkeep"):
                try:
                    os.remove(f)
                except Exception:
                    pass

        return jsonify({
            "success": True,
            "message": "Knowledge base and uploaded files cleared successfully.",
            "total_chunks": 0,
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
