

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
    last_error = None
    encodings = ["utf-8-sig", "utf-8", "latin-1"]
    separators = [None, ",", ";", "\t", "|"]

    for encoding in encodings:
        for separator in separators:
            try:
                options = {"encoding": encoding, "on_bad_lines": "skip"}
                if separator is None:
                    options["sep"] = None
                    options["engine"] = "python"
                else:
                    options["sep"] = separator
                df = pd.read_csv(csv_path, **options)
                if len(df.columns) > 1 or not df.empty:
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
        elif kind == "generic":
            df_masked[col] = df_masked[col].apply(_mask_value)
    return df_masked


def mask_sensitive_columns(csv_file: str | Path) -> Path:
    csv_path = Path(csv_file)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV file not found: {csv_path}")

    output_path = config.OUTPUT_DIR / f"{csv_path.stem}_masked.csv"
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    df = _read_csv_flexible(csv_path)
    df_masked = mask_dataframe(df)

    df_masked.to_csv(output_path, index=False)
    return output_path
