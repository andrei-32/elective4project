"""Tests for verify_file_integrity."""

import pytest
from src.generate_checksum import generate_checksum
from src.verify_file_integrity import verify_file_integrity


def test_verify_file_integrity_first_run(sample_csv, input_output_dirs):
    """First run generates checksum and passes."""
    input_dir, output_dir = input_output_dirs
    csv_path = input_dir / "sample.csv"
    csv_path.write_text(sample_csv.read_text())

    result = verify_file_integrity(csv_path)

    assert result is True
    checksum_path = output_dir / "sample.checksum"
    assert checksum_path.exists()


def test_verify_file_integrity_unchanged_file(sample_csv, input_output_dirs):
    """Unchanged file should verify successfully."""
    input_dir, output_dir = input_output_dirs
    csv_path = input_dir / "sample.csv"
    csv_path.write_text(sample_csv.read_text())
    generate_checksum(csv_path)

    assert verify_file_integrity(csv_path) is True


def test_verify_file_integrity_tampered_file(sample_csv, input_output_dirs):
    """Tampered file triggers checksum regeneration (verify passes, checksum updated)."""
    input_dir, output_dir = input_output_dirs
    csv_path = input_dir / "sample.csv"
    csv_path.write_text(sample_csv.read_text())
    generate_checksum(csv_path)
    old_checksum = (output_dir / "sample.checksum").read_text()

    csv_path.write_text(sample_csv.read_text() + "\nTampered,row,123,999")

    assert verify_file_integrity(csv_path) is True
    new_checksum = (output_dir / "sample.checksum").read_text()
    assert new_checksum != old_checksum


def test_verify_file_integrity_file_not_found():
    """Should raise FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError, match="not found"):
        verify_file_integrity("/nonexistent/file.csv")
