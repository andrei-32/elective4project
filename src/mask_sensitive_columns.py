"""Mask sensitive columns in CSV files."""

from pathlib import Path

import pandas as pd

from . import config


def _is_sensitive_column(column_name: str) -> bool:
    """Check if a column name indicates sensitive data."""
    col_lower = column_name.lower().replace(" ", "_").replace("-", "_")
    return any(pattern in col_lower for pattern in config.SENSITIVE_COLUMN_PATTERNS)


def _mask_value(value: str, mask_char: str = "*") -> str:
    """
    Mask a string value, preserving some structure for readability.
    Keeps first/last chars for short strings, masks middle for longer.
    """
    if pd.isna(value):
        return value
    value_str = str(value).strip()
    if not value_str:
        return value_str
    if len(value_str) <= 2:
        return mask_char * len(value_str)
    if len(value_str) <= 4:
        return value_str[0] + mask_char * (len(value_str) - 1)
    # Show first 2 and last 2 chars for longer strings
    visible_start = min(2, len(value_str) // 2)
    visible_end = min(2, len(value_str) - visible_start - 1)
    return (
        value_str[:visible_start]
        + mask_char * (len(value_str) - visible_start - visible_end)
        + value_str[-visible_end:]
    )


def mask_sensitive_columns(csv_file: str | Path) -> Path:
    """
    Mask sensitive columns in a CSV file and save the result.

    Args:
        csv_file: Path to the CSV file to process.

    Returns:
        Path to the masked CSV output file.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
    """
    csv_path = Path(csv_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    output_path = config.OUTPUT_DIR / f"{csv_path.stem}_masked.csv"
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(csv_path)

    for col in df.columns:
        if _is_sensitive_column(col):
            df[col] = df[col].apply(_mask_value)

    df.to_csv(output_path, index=False)
    return output_path
