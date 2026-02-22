"""Pytest fixtures for CSV processing tests."""

import tempfile
from pathlib import Path

import pytest

# Add project root to path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))


@pytest.fixture
def sample_csv(tmp_path):
    """Create a sample CSV file with sensitive columns."""
    csv_path = tmp_path / "sample.csv"
    csv_path.write_text(
        "name,email,ssn,amount\n"
        "Alice,alice@example.com,123-45-6789,100\n"
        "Bob,bob@example.com,987-65-4321,200\n"
    )
    return csv_path


@pytest.fixture
def input_output_dirs(tmp_path, monkeypatch):
    """Set up input/ and output/ directories for processing tests."""
    input_dir = tmp_path / "input"
    output_dir = tmp_path / "output"
    input_dir.mkdir()
    output_dir.mkdir()

    import src.config as config
    monkeypatch.setattr(config, "INPUT_DIR", input_dir)
    monkeypatch.setattr(config, "OUTPUT_DIR", output_dir)

    return input_dir, output_dir
