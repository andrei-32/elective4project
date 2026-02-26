
"""Encrypt CSV file output using Fernet symmetric encryption."""

import io
from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

from . import config


def encrypt_csv_output(csv_file: str | Path) -> Path:

    """
    Encrypt a CSV file and save the encrypted output.

    Args:
        csv_file: Path to the CSV file to encrypt.

    Returns:
        Path to the encrypted output file.

    Raises:
        ValueError: If encryption key is not configured.
        FileNotFoundError: If the CSV file does not exist.
    """

    csv_path = Path(csv_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    if config.DEFAULT_KEY is None:
        raise ValueError(
            "Encryption key not configured. Set ENCRYPTION_KEY environment variable."
        )

    output_path = config.OUTPUT_DIR / f"{csv_path.stem}_encrypted.bin"
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    key = config.DEFAULT_KEY
    fernet = Fernet(key.encode() if isinstance(key, str) else key)

    with open(csv_path, "rb") as f:
        data = f.read()

    encrypted_data = fernet.encrypt(data)

    with open(output_path, "wb") as f:
        f.write(encrypted_data)

    return output_path





