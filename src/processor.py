"""Main orchestrator - processes all CSV files from input folder to output folder."""

import logging
import os
from pathlib import Path

from . import config
from .mask_sensitive_columns import mask_sensitive_columns
from .generate_checksum import generate_checksum
from .verify_file_integrity import verify_file_integrity
from .encrypt_csv import encrypt_csv_output
from .decrypt_csv import decrypt_csv_output

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CSV_EXTENSIONS = {".csv"}
ENCRYPTED_EXTENSION = ".bin"


def process_all_csv_files(skip_encryption: bool = True) -> list[dict]:
    """
    Process all CSV files in the input directory.

    Pipeline for each CSV:
    1. Verify integrity (or generate checksum if first run)
    2. Mask sensitive columns
    3. Generate checksum for masked output
    4. Optionally encrypt (requires ENCRYPTION_KEY)

    Args:
        skip_encryption: If True, skip encrypt/decrypt when key not set (default for CI).

    Returns:
        List of results per file with status and output paths.
    """
    config.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    csv_files = [f for f in config.INPUT_DIR.iterdir() if f.suffix.lower() == ".csv"]

    if not csv_files:
        logger.info("No CSV files found in input directory.")
        return results

    for csv_path in csv_files:
        result = {"file": str(csv_path.name), "status": "ok", "outputs": []}
        try:
            # 1. Verify / generate checksum for original
            if verify_file_integrity(csv_path):
                result["outputs"].append("integrity_verified")
            else:
                result["status"] = "integrity_failed"
                result["outputs"].append("integrity_verification_failed")
                results.append(result)
                continue

            # 2. Mask sensitive columns
            masked_path = mask_sensitive_columns(csv_path)
            result["outputs"].append(str(masked_path.name))

            # 3. Generate checksum for masked output
            checksum_path, _ = generate_checksum(masked_path)
            result["outputs"].append(str(checksum_path.name))

            # 4. Encrypt (optional, when key is available)
            if not skip_encryption:
                try:
                    enc_path = encrypt_csv_output(masked_path)
                    result["outputs"].append(str(enc_path.name))
                except ValueError as e:
                    if "Encryption key not configured" in str(e):
                        logger.warning("Skipping encryption: %s", e)
                    else:
                        raise

        except Exception as e:
            logger.exception("Error processing %s", csv_path.name)
            result["status"] = "error"
            result["error"] = str(e)

        results.append(result)

    return results


def run() -> int:
    """
    Entry point for the pipeline. Returns exit code (0 = success).
    """
    skip_encryption = config.DEFAULT_KEY is None
    if skip_encryption:
        logger.info("ENCRYPTION_KEY not set - encryption/decryption will be skipped.")
        # Fail when encryption is required for compliance (e.g. on push to main)
        if os.environ.get("REQUIRE_ENCRYPTION", "").lower() in ("true", "1", "yes"):
            logger.error(
                "REQUIRE_ENCRYPTION is set but ENCRYPTION_KEY is missing. "
                "Configure ENCRYPTION_KEY (env var locally, GitHub Secrets in CI). Aborting."
            )
            return 1

    results = process_all_csv_files(skip_encryption=skip_encryption)
    has_errors = any(r["status"] != "ok" for r in results)

    for r in results:
        logger.info("%s: %s -> %s", r["file"], r["status"], r.get("outputs", []))

    return 1 if has_errors else 0
