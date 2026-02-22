"""Tests for mask_sensitive_columns."""

import pytest
from src.mask_sensitive_columns import mask_sensitive_columns


def test_mask_sensitive_columns(sample_csv, input_output_dirs):
    """Sensitive columns should be masked."""
    input_dir, output_dir = input_output_dirs
    csv_path = input_dir / "sample.csv"
    csv_path.write_text(sample_csv.read_text())

    result = mask_sensitive_columns(csv_path)

    assert result.exists()
    assert result.suffix == ".csv"
    content = result.read_text()
    # SSN and email should be masked (show partial, mask middle)
    assert "123-45-6789" not in content or "****" in content
    assert "alice@example.com" not in content or "****" in content
    # name and amount may or may not be masked depending on config
    assert "Alice" in content
    assert "100" in content


def test_mask_sensitive_columns_file_not_found(input_output_dirs):
    """Should raise FileNotFoundError for missing file."""
    with pytest.raises(FileNotFoundError, match="not found"):
        mask_sensitive_columns("/nonexistent/file.csv")
