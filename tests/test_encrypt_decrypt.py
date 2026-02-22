"""Tests for encrypt_csv_output and decrypt_csv_output."""

import os
import pytest
from cryptography.fernet import Fernet

from src.encrypt_csv import encrypt_csv_output
from src.decrypt_csv import decrypt_csv_output


@pytest.fixture
def encryption_key(monkeypatch):
    """Set up encryption key for tests."""
    key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    import src.config as config
    config.DEFAULT_KEY = key
    return key


def test_encrypt_decrypt_roundtrip(sample_csv, input_output_dirs, encryption_key):
    """Encrypted file should decrypt back to original content."""
    input_dir, output_dir = input_output_dirs
    csv_path = input_dir / "sample.csv"
    original_content = sample_csv.read_text()
    csv_path.write_text(original_content)

    enc_path = encrypt_csv_output(csv_path)
    assert enc_path.exists()
    assert enc_path.suffix == ".bin"

    dec_path = decrypt_csv_output(enc_path)
    assert dec_path.exists()
    assert dec_path.suffix == ".csv"
    assert dec_path.read_text() == original_content


def test_encrypt_without_key(sample_csv, input_output_dirs, monkeypatch):
    """Should raise ValueError when encryption key not set."""
    monkeypatch.delenv("ENCRYPTION_KEY", raising=False)
    import src.config as config
    config.DEFAULT_KEY = None

    input_dir, output_dir = input_output_dirs
    csv_path = input_dir / "sample.csv"
    csv_path.write_text(sample_csv.read_text())

    with pytest.raises(ValueError, match="Encryption key not configured"):
        encrypt_csv_output(csv_path)


def test_decrypt_wrong_key(sample_csv, input_output_dirs):
    """Decryption with wrong key should raise ValueError."""
    key1 = Fernet.generate_key()
    key2 = Fernet.generate_key()
    import src.config as config
    config.DEFAULT_KEY = key1.decode()

    input_dir, output_dir = input_output_dirs
    csv_path = input_dir / "sample.csv"
    csv_path.write_text(sample_csv.read_text())

    enc_path = encrypt_csv_output(csv_path)
    config.DEFAULT_KEY = key2.decode()

    with pytest.raises(ValueError, match="Decryption failed"):
        decrypt_csv_output(enc_path)
