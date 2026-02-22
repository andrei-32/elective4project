"""Decrypt CSV file output."""

from pathlib import Path

from cryptography.fernet import Fernet, InvalidToken

from . import config


def decrypt_csv_output(csv_file: str | Path) -> Path:
    """
    Decrypt an encrypted CSV file and save the plaintext output.

    Args:
        csv_file: Path to the encrypted file (.bin) to decrypt.

    Returns:
        Path to the decrypted CSV output file.

    Raises:
        ValueError: If decryption key is not configured or decryption fails.
        FileNotFoundError: If the encrypted file does not exist.
    """
    encrypted_path = Path(csv_file)
    if not encrypted_path.exists():
        raise FileNotFoundError(f"Encrypted file not found: {encrypted_path}")

    if config.DEFAULT_KEY is None:
        raise ValueError(
            "Decryption key not configured. Set ENCRYPTION_KEY environment variable."
        )

    output_path = config.OUTPUT_DIR / f"{encrypted_path.stem.replace('_encrypted', '_decrypted')}.csv"
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    key = config.DEFAULT_KEY
    fernet = Fernet(key.encode() if isinstance(key, str) else key)

    with open(encrypted_path, "rb") as f:
        encrypted_data = f.read()

    try:
        decrypted_data = fernet.decrypt(encrypted_data)
    except InvalidToken:
        raise ValueError("Decryption failed. Invalid or wrong encryption key.")

    with open(output_path, "wb") as f:
        f.write(decrypted_data)

    return output_path
