"""Verify file integrity using stored checksum."""

import hashlib
from pathlib import Path

from . import config
from .generate_checksum import generate_checksum


def verify_file_integrity(csv_file: str | Path) -> bool:
    """
    Verify a file's integrity by comparing against its stored checksum.

    If no checksum file exists, one is generated and verification passes.

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

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    actual_checksum = sha256_hash.hexdigest()
    return actual_checksum == expected_checksum
