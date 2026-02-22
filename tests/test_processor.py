"""Tests for main processor pipeline."""

import pytest
from src.processor import process_all_csv_files


def test_process_all_empty_input(input_output_dirs):
    """Empty input directory should return empty results."""
    input_dir, output_dir = input_output_dirs
    results = process_all_csv_files(skip_encryption=True)
    assert results == []


def test_process_all_csv_files(sample_csv, input_output_dirs):
    """Pipeline should process CSV and produce masked output and checksums."""
    input_dir, output_dir = input_output_dirs
    csv_path = input_dir / "sample.csv"
    csv_path.write_text(sample_csv.read_text())

    results = process_all_csv_files(skip_encryption=True)

    assert len(results) == 1
    assert results[0]["status"] == "ok"
    assert "sample_masked.csv" in results[0]["outputs"]
    assert (output_dir / "sample_masked.csv").exists()
    assert (output_dir / "sample_masked.checksum").exists()


def test_process_all_integrity_failed(sample_csv, input_output_dirs):
    """Pipeline should flag integrity_failed when file is tampered after checksum."""
    input_dir, output_dir = input_output_dirs
    csv_path = input_dir / "sample.csv"
    csv_path.write_text(sample_csv.read_text())
    from src.generate_checksum import generate_checksum

    generate_checksum(csv_path)  # Create checksum
    csv_path.write_text(sample_csv.read_text() + "\nTampered,data,xxx,0")  # Tamper

    results = process_all_csv_files(skip_encryption=True)

    assert len(results) == 1
    assert results[0]["status"] == "integrity_failed"
    assert "integrity_verification_failed" in results[0]["outputs"]
    assert not (output_dir / "sample_masked.csv").exists()


def test_process_bin_file_skipped_without_key(input_output_dirs):
    """Pipeline should skip .bin files when ENCRYPTION_KEY is not set."""
    input_dir, output_dir = input_output_dirs
    # Create a dummy .bin file (invalid encrypted content, but we skip before decrypt)
    (input_dir / "data_encrypted.bin").write_bytes(b"dummy")

    results = process_all_csv_files(skip_encryption=True)

    assert len(results) == 1
    assert results[0]["file"] == "data_encrypted.bin"
    assert results[0]["status"] == "skipped"
    assert "decryption_skipped_no_key" in results[0]["outputs"]


def test_process_bin_file_decrypts_with_key(sample_csv, input_output_dirs, monkeypatch):
    """Pipeline should decrypt .bin files when ENCRYPTION_KEY is set."""
    from cryptography.fernet import Fernet

    key = Fernet.generate_key().decode()
    monkeypatch.setenv("ENCRYPTION_KEY", key)
    import src.config as config
    config.DEFAULT_KEY = key

    input_dir, output_dir = input_output_dirs
    # Create encrypted .bin from sample content
    fernet = Fernet(key.encode())
    encrypted = fernet.encrypt(sample_csv.read_text().encode())
    (input_dir / "sample_encrypted.bin").write_bytes(encrypted)

    results = process_all_csv_files(skip_encryption=False)

    assert len(results) == 1
    assert results[0]["status"] == "ok"
    assert "sample_decrypted.csv" in results[0]["outputs"]
    dec_path = output_dir / "sample_decrypted.csv"
    assert dec_path.exists()
    assert dec_path.read_text() == sample_csv.read_text()
