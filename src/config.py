"""Configuration for CSV processing pipeline."""

import os
from pathlib import Path

# Project paths (relative to project root)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_DIR = PROJECT_ROOT / "input"
OUTPUT_DIR = PROJECT_ROOT / "output"

# Encryption key - use env var ENCRYPTION_KEY for production/CI
# Generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
_key = os.environ.get("ENCRYPTION_KEY") or ""
DEFAULT_KEY = _key.strip() or None

# Columns to mask (case-insensitive partial match)
SENSITIVE_COLUMN_PATTERNS = [
    "ssn", "social_security", "credit_card", "cc_number", "card_number",
    "password", "secret", "api_key", "token", "email", "phone", "dob",
    "student_id", "studentid", "id_number", "identifier"
]

# Checksum file extension
CHECKSUM_EXT = ".checksum"
