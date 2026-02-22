"""Generate checksum for CSV files."""

import hashlib
from pathlib import Path

from . import config


def generate_checksum(csv_file: str | Path) -> tuple[Path, str]:
    """
    Generate SHA-256 checksum for a file and save it.

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

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)

    checksum = sha256_hash.hexdigest()

    # Save checksum alongside the file (same stem, .checksum extension)
    output_path = config.OUTPUT_DIR / f"{file_path.stem}{config.CHECKSUM_EXT}"
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w") as f:
        f.write(checksum)

    return output_path, checksum
