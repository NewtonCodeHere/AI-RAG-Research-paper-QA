# AI Research Paper Assistant using RAG

**Author:** NewtonCode (Mani Barathi P)  
**Organization:** CodeBind Technologies  
**Role:** Artificial Intelligence Intern (4 Weeks)

## Overview

AI Research Paper Assistant is a Retrieval-Augmented Generation (RAG) based web application that enables users to upload research paper PDFs and ask questions in natural language. The system retrieves relevant document sections using semantic search and generates context-aware answers using Google's Gemini Large Language Model.

## Features

- Upload one or more research paper PDFs
- Extract text from uploaded documents
- Automatic text chunking and embedding generation
- Semantic search using vector embeddings
- Context-aware question answering using Gemini
- Displays source page references
- Simple chat interface with session history

## Tech Stack

| Layer | Technology |
|--------|------------|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, Flask |
| LLM Framework | LangChain |
| LLM | Google Gemini API |
| Embeddings | Hugging Face Sentence Transformers |
| Vector Database | ChromaDB |
| PDF Processing | PyPDF2 |

## Project Structure

```text
AI-Research-Paper-Assistant/
│
├── app.py
├── requirements.txt
├── README.md
│
├── static/
│   ├── style.css
│   └── script.js
│
├── templates/
│   └── index.html
│
├── uploads/
├── data/
│
├── rag/
│   ├── pdf_loader.py
│   ├── chunking.py
│   ├── embeddings.py
│   ├── vector_store.py
│   └── qa_chain.py
│
└── utils/
    └── helpers.py
```

## Installation

### Clone Repository

```bash
git clone https://github.com/NewtonCodeHere/AI-RAG-Research-paper-QA.git
cd AI-RAG-Research-paper-QA
```

### Create Virtual Environment

```bash
python -m venv venv
```

**Windows**

```bash
venv\Scripts\activate
```

**Linux / macOS**

```bash
source venv/bin/activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Configure Environment

Create a `.env` file in the project root.

```env
GEMINI_API_KEY=YOUR_API_KEY
FLASK_SECRET_KEY=YOUR_SECRET_KEY
```

### Run the Application

```bash
python app.py
```

Open your browser and visit

```
http://127.0.0.1:5000
```

---

# RAG Workflow

1. Upload research paper PDFs.
2. Extract text using **PyPDF2**.
3. Split text into overlapping chunks.
4. Generate embeddings using **Sentence Transformers**.
5. Store embeddings in **ChromaDB**.
6. Retrieve relevant chunks through semantic similarity.
7. Generate grounded answers using **Google Gemini**.

---

## Future Improvements

- Multi-user authentication
- Conversation memory
- Support for larger document collections
- Citation highlighting
- Research paper summarization
- PDF annotation support

---

## Resume Description

> Developed a RAG-based assistant for semantic retrieval and LLM-powered question answering over research papers.

---

## Author

**Mani Barathi P (NewtonCode)**

Artificial Intelligence Intern  
CodeBind Technologies
