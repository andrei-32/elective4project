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
