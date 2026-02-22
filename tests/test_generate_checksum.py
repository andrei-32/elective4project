"""Tests for generate_checksum."""

import pytest
from src.generate_checksum import generate_checksum


def test_generate_checksum(sample_csv, input_output_dirs):
    """Checksum file should be created with valid SHA-256 hash."""
    input_dir, output_dir = input_output_dirs
    csv_path = input_dir / "sample.csv"
    csv_path.write_text(sample_csv.read_text())

    checksum_path, checksum = generate_checksum(csv_path)

    assert checksum_path.exists()
    assert checksum_path.suffix == ".checksum"
    assert len(checksum) == 64
    assert all(c in "0123456789abcdef" for c in checksum)
    assert checksum_path.read_text().strip() == checksum


def test_generate_checksum_deterministic(sample_csv, input_output_dirs):
    """Same file should produce same checksum."""
    input_dir, output_dir = input_output_dirs
    csv_path = input_dir / "sample.csv"
    csv_path.write_text(sample_csv.read_text())

    _, c1 = generate_checksum(csv_path)
    _, c2 = generate_checksum(csv_path)

    assert c1 == c2


def test_generate_checksum_file_not_found():
    """Should raise FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError, match="not found"):
        generate_checksum("/nonexistent/file.csv")
