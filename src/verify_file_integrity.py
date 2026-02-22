"""Verify file integrity using stored checksum."""

import hashlib
from pathlib import Path

from . import config
from .generate_checksum import generate_checksum, _normalize_for_hash


def verify_file_integrity(csv_file: str | Path) -> bool:
    """
    Verify a file's integrity by comparing against its stored checksum.

    If no checksum file exists, one is generated and verification passes.
    Text files use normalized line endings for cross-platform consistency.

    Args:
        csv_file: Path to the file to verify.

    Returns:
        True if the file integrity is verified (or checksum is newly created),
        False if the file does not match the stored checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(csv_file)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Look for checksum in output dir (same stem as file)
    checksum_path = config.OUTPUT_DIR / f"{file_path.stem}{config.CHECKSUM_EXT}"

    if not checksum_path.exists():
        # Generate checksum for the first time
        generate_checksum(file_path)
        return True

    with open(checksum_path, "r") as f:
        expected_checksum = f.read().strip()

    data = file_path.read_bytes()
    normalized = _normalize_for_hash(data)
    actual_checksum = hashlib.sha256(normalized).hexdigest()

    return actual_checksum == expected_checksum
