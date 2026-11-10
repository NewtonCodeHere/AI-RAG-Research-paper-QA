"""
Helper utilities for file handling, validation, formatting, and environment checks.
"""

import os
import re
from datetime import datetime
from typing import Dict, Any, Tuple
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = {"pdf"}
MAX_FILE_SIZE_MB = 50


def allowed_file(filename: str) -> bool:
    """Checks if the uploaded file has an allowed PDF extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def sanitize_filename(filename: str) -> str:
    """Sanitizes filename and replaces whitespace while preserving readability."""
    clean = secure_filename(filename)
    if not clean:
        clean = "research_paper.pdf"
    return clean


def format_file_size(size_bytes: int) -> str:
    """Formats raw byte sizes into human-readable strings (KB, MB)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    else:
        return f"{size_bytes / (1024 * 1024):.2f} MB"


def get_current_timestamp() -> str:
    """Returns ISO format timestamp for message tracking."""
    return datetime.now().strftime("%I:%M %p")


def validate_environment() -> Tuple[bool, str]:
    """Validates required environment variables."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key or gemini_key == "YOUR_API_KEY":
        return False, "GEMINI_API_KEY is not configured in .env. Please set a valid Google Gemini API key."
    return True, "Environment configured successfully."
