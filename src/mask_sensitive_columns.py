

"""
Mask sensitive columns in CSV files
"""

import re
from pathlib import Path
import pandas as pd
from . import config


def _sensitive_kind(column_name: str) -> str | None:
    col_lower = column_name.lower().replace(" ", "_").replace("-", "_")
    if "email" in col_lower:
        return "email"
    if "ssn" in col_lower or "social_security" in col_lower:
        return "ssn"
    if "credit_card" in col_lower or "cc_number" in col_lower or "card_number" in col_lower:
        return "card"
    if "phone" in col_lower:
        return "phone"
    if "identifier" in col_lower or "id_number" in col_lower or "student_id" in col_lower or "studentid" in col_lower:
        return "identifier"
    return "generic" if any(pattern in col_lower for pattern in config.SENSITIVE_COLUMN_PATTERNS) else None


def _is_sensitive_column(column_name: str) -> bool:
    return _sensitive_kind(column_name) is not None


def _mask_value(value: str, mask_char: str = "*") -> str:
    if pd.isna(value):
        return value
    value_str = str(value).strip()
    if not value_str:
        return value_str
    if len(value_str) <= 2:
        return mask_char * len(value_str)
    if len(value_str) <= 4:
        return value_str[0] + mask_char * (len(value_str) - 1)
    visible_start = min(2, len(value_str) // 2)
    visible_end = min(2, len(value_str) - visible_start - 1)
    return (
        value_str[:visible_start]
        + mask_char * (len(value_str) - visible_start - visible_end)
        + value_str[-visible_end:]
    )


def _mask_email(value: str) -> str:
    if pd.isna(value):
        return value
    value_str = str(value).strip()
    if "@" not in value_str:
        return _mask_value(value_str)
    local, domain = value_str.split("@", 1)
    local_masked = local[0] + "*" * max(0, len(local) - 1) if local else ""
    if "." in domain:
        domain_name, domain_ext = domain.rsplit(".", 1)
        domain_masked = (
            (domain_name[0] + "*" * max(0, len(domain_name) - 1))
            if domain_name
            else ""
        )
        return f"{local_masked}@{domain_masked}.{domain_ext}"
    domain_masked = domain[0] + "*" * max(0, len(domain) - 1) if domain else ""
    return f"{local_masked}@{domain_masked}"


def _mask_ssn(value: str) -> str:
    if pd.isna(value):
        return value
    digits = re.sub(r"\D", "", str(value))
    if len(digits) < 4:
        return "*" * len(digits)
    return f"***-**-{digits[-4:]}"


def _mask_credit_card(value: str) -> str:
    if pd.isna(value):
        return value
    digits = re.sub(r"\D", "", str(value))
    if not digits:
        return ""
    masked = "*" * max(0, len(digits) - 4) + digits[-4:]
    grouped = " ".join(masked[i : i + 4] for i in range(0, len(masked), 4))
    return grouped


def _mask_phone(value: str) -> str:
    if pd.isna(value):
        return value
    digits = re.sub(r"\D", "", str(value))
    if len(digits) <= 3:
        return "*" * len(digits)
    return "*" * (len(digits) - 3) + digits[-3:]


def _read_csv_flexible(csv_path: Path) -> pd.DataFrame:
    """
    Try to read a CSV with various encodings and delimiters. Handles mixed delimiters and scientific notation.
    """
    import csv
    last_error = None
    encodings = ["utf-8-sig", "utf-8", "latin-1"]
    delimiters = [",", ";", "\t", "|"]

    # Try pandas default first
    for encoding in encodings:
        try:
            df = pd.read_csv(csv_path, encoding=encoding, on_bad_lines="skip")
            if len(df.columns) > 1 and not df.empty:
                return df
        except Exception as exc:
            last_error = exc

    # Try with explicit delimiters
    for encoding in encodings:
        for delimiter in delimiters:
            try:
                df = pd.read_csv(csv_path, encoding=encoding, sep=delimiter, on_bad_lines="skip")
                if len(df.columns) > 1 and not df.empty:
                    return df
            except Exception as exc:
                last_error = exc

    # Try csv.Sniffer to auto-detect delimiter
    for encoding in encodings:
        try:
            with open(csv_path, "r", encoding=encoding) as f:
                sample = f.read(2048)
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample)
                df = pd.read_csv(csv_path, encoding=encoding, sep=dialect.delimiter, on_bad_lines="skip")
                if len(df.columns) > 1 and not df.empty:
                    return df
        except Exception as exc:
            last_error = exc

    if last_error is not None:
        raise ValueError(f"Unable to parse CSV file: {csv_path}") from last_error
    raise ValueError(f"Unable to parse CSV file: {csv_path}")


def mask_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    df_masked = df.copy()
    for col in df_masked.columns:
        kind = _sensitive_kind(col)
        if kind == "email":
            df_masked[col] = df_masked[col].apply(_mask_email)
        elif kind == "ssn":
            df_masked[col] = df_masked[col].apply(_mask_ssn)
        elif kind == "card":
            df_masked[col] = df_masked[col].apply(_mask_credit_card)
        elif kind == "phone":
            df_masked[col] = df_masked[col].apply(_mask_phone)
        elif kind == "identifier":
            # Mask identifier columns, preserving scientific notation as string
            def mask_identifier(val):
                if pd.isna(val):
                    return val
                val_str = str(val)
                # If scientific notation, keep as string and mask all but last 3 digits
                if "e" in val_str.lower():
                    digits = re.sub(r"\D", "", val_str)
                    if len(digits) > 3:
                        return "*" * (len(digits) - 3) + digits[-3:]
                    return "*" * len(digits)
                # Otherwise, mask as normal
                return _mask_value(val_str)
            df_masked[col] = df_masked[col].apply(mask_identifier)
        elif kind == "generic":
            df_masked[col] = df_masked[col].apply(_mask_value)
    return df_masked


def mask_sensitive_columns(csv_file: str | Path, output_dir: Path | None = None) -> Path:
    csv_path = Path(csv_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    target_dir = output_dir or config.OUTPUT_DIR
    output_path = target_dir / f"{csv_path.stem}_masked.csv"
    target_dir.mkdir(parents=True, exist_ok=True)

    df = _read_csv_flexible(csv_path)
    df_masked = mask_dataframe(df)

    df_masked.to_csv(output_path, index=False)
    return output_path
