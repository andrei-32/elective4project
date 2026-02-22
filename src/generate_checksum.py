"""Generate checksum for CSV files."""

import hashlib
from pathlib import Path

from . import config


def _normalize_for_hash(data: bytes) -> bytes:
    """
    Normalize line endings for consistent checksums across platforms (Windows/Linux/Mac).
    Prevents integrity failures when git converts CRLF <-> LF.
    """
    try:
        text = data.decode("utf-8")
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        return normalized.encode("utf-8")
    except UnicodeDecodeError:
        return data  # Binary file, hash as-is


def generate_checksum(csv_file: str | Path) -> tuple[Path, str]:
    """
    Generate SHA-256 checksum for a file and save it.

    Text/CSV files are normalized (line endings) for cross-platform consistency.

    Args:
        csv_file: Path to the file to checksum.

    Returns:
        Tuple of (path to checksum file, the checksum string).

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(csv_file)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    data = file_path.read_bytes()
    normalized = _normalize_for_hash(data)
    checksum = hashlib.sha256(normalized).hexdigest()

    # Save checksum alongside the file (same stem, .checksum extension)
    output_path = config.OUTPUT_DIR / f"{file_path.stem}{config.CHECKSUM_EXT}"
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write(checksum)

    return output_path, checksum
