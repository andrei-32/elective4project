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


def _process_csv_file(csv_path: Path, skip_encryption: bool) -> dict:
    """Process a single CSV: verify → encrypt/decrypt (unmasked) → mask → checksum."""
    result = {"file": str(csv_path.name), "status": "ok", "outputs": []}
    try:
        if not verify_file_integrity(csv_path):
            result["status"] = "integrity_failed"
            result["outputs"].append("integrity_verification_failed")
            return result

        result["outputs"].append("integrity_verified")

        # First, encrypt and decrypt the original (unmasked) data to demonstrate encryption works
        if not skip_encryption:
            try:
                enc_path_original = encrypt_csv_output(csv_path)
                result["outputs"].append(str(enc_path_original.name))
                # Decrypt to get unmasked version (proves encrypt/decrypt works)
                dec_path_unmasked = decrypt_csv_output(enc_path_original, mask=False)
                result["outputs"].append(str(dec_path_unmasked.name))
            except ValueError as e:
                if "Encryption key not configured" in str(e):
                    logger.warning("Skipping encryption: %s", e)
                else:
                    raise

        # Now mask the original CSV for security
        masked_path = mask_sensitive_columns(csv_path)
        result["outputs"].append(str(masked_path.name))

        checksum_path, _ = generate_checksum(masked_path)
        result["outputs"].append(str(checksum_path.name))

    except Exception as e:
        logger.exception("Error processing %s", csv_path.name)
        result["status"] = "error"
        result["error"] = str(e)

    return result


def _process_encrypted_file(bin_path: Path, skip_encryption: bool) -> dict:
    """Process a single .bin file: decrypt (unmasked & masked) → checksum."""
    result = {"file": str(bin_path.name), "status": "ok", "outputs": []}
    try:
        if skip_encryption:
            result["status"] = "skipped"
            result["outputs"].append("decryption_skipped_no_key")
            return result

        # Generate both unmasked and masked versions
        dec_path_unmasked = decrypt_csv_output(bin_path, mask=False)
        result["outputs"].append(str(dec_path_unmasked.name))

        dec_path_masked = decrypt_csv_output(bin_path, mask=True)
        result["outputs"].append(str(dec_path_masked.name))

        checksum_path, _ = generate_checksum(dec_path_masked)
        result["outputs"].append(str(checksum_path.name))

    except Exception as e:
        logger.exception("Error decrypting %s", bin_path.name)
        result["status"] = "error"
        result["error"] = str(e)

    return result


def process_all_csv_files(skip_encryption: bool = True) -> list[dict]:
    """
    Process all files in the input and output directories (dual-mode pipeline).

    - .csv in input/: verify → mask → checksum → encrypt → decrypt
    - .bin in input/: decrypt → checksum (requires ENCRYPTION_KEY)
    - .bin in output/: decrypt if no _decrypted.csv exists yet

    Args:
        skip_encryption: If True, skip encrypt/decrypt when key not set (default for CI).

    Returns:
        List of results per file with status and output paths.
    """
    config.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    results = []
    csv_files = [f for f in config.INPUT_DIR.iterdir() if f.suffix.lower() == ".csv"]
    bin_in_input = [f for f in config.INPUT_DIR.iterdir() if f.suffix.lower() == ".bin"]
    bin_in_output = [f for f in config.OUTPUT_DIR.iterdir() if f.suffix.lower() == ".bin"]

    if not csv_files and not bin_in_input and not bin_in_output:
        logger.info("No CSV or .bin files found in input or output directory.")
        return results

    for csv_path in csv_files:
        results.append(_process_csv_file(csv_path, skip_encryption))

    for bin_path in bin_in_input:
        results.append(_process_encrypted_file(bin_path, skip_encryption))

    # Decrypt .bin files in output/ (e.g. from previous commits or same run)
    for bin_path in bin_in_output:
        dec_name = bin_path.stem.replace("_encrypted", "_decrypted") + ".csv"
        dec_path = config.OUTPUT_DIR / dec_name
        if dec_path.exists():
            continue  # Already decrypted
        results.append(_process_encrypted_file(bin_path, skip_encryption))

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
    has_errors = any(r["status"] in ("integrity_failed", "error") for r in results)

    for r in results:
        logger.info("%s: %s -> %s", r["file"], r["status"], r.get("outputs", []))

    return 1 if has_errors else 0
