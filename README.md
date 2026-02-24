# CSV Data Processing Application

A Python-based CSV data processing pipeline that automatically processes CSV files from the `input/` folder and saves results to the `output/` folder. Integrated with GitHub Actions for CI/CD automation.

## Features

- **5 processing functions** (each in a separate module):
  1. `encrypt_csv_output(csv_file)` – Encrypt CSV using Fernet symmetric encryption
  2. `decrypt_csv_output(csv_file)` – Decrypt previously encrypted files
  3. `mask_sensitive_columns(csv_file)` – Mask SSN, email, credit card, and similar columns
  4. `generate_checksum(csv_file)` – Generate SHA-256 checksum for integrity
  5. `verify_file_integrity(csv_file)` – Verify file against stored checksum

- **Automated pipeline** – Runs on every push and pull request via GitHub Actions
- **DevOps-ready** – Demonstrates CI/CD, automated testing, and collaboration

## Project Structure

```
elective4project/
├── input/              # Place CSV or .bin files here (dual-mode pipeline)
├── output/             # Processed files appear here
├── src/
│   ├── encrypt_csv.py          # encrypt_csv_output()
│   ├── decrypt_csv.py          # decrypt_csv_output()
│   ├── mask_sensitive_columns.py
│   ├── generate_checksum.py
│   ├── verify_file_integrity.py
│   ├── processor.py    # Main orchestrator
│   └── config.py
├── tests/
├── main.py
├── requirements.txt
└── .github/workflows/ci-csv-process.yml
```

## Quick Start

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Add files** to the `input/` folder:
   - **.csv** → mask, checksum, encrypt
   - **.bin** (encrypted) → decrypt, checksum (requires ENCRYPTION_KEY)

3. **Run the pipeline**
   ```bash
   python main.py
   ```

4. **View results** in the `output/` folder

## Example Input/Output

**Sample input CSV (`input/test.csv`):**

| Name         | SSN         | Email              | Credit Card     |
|--------------|-------------|--------------------|----------------|
| Alice Smith  | 123-45-6789 | alice@email.com    | 4111 1111 1111 1111 |
| Bob Johnson  | 987-65-4321 | bob@email.com      | 5500 0000 0000 0004 |

**Sample masked output (`output/test_masked.csv`):**

| Name         | SSN         | Email              | Credit Card     |
|--------------|-------------|--------------------|----------------|
| Alice Smith  | ***-**-6789 | a****@e****.com    | **** **** **** 1111 |
| Bob Johnson  | ***-**-4321 | b****@e****.com    | **** **** **** 0004 |

**Sample checksum output (`output/test.checksum`):**
```
SHA256 (test_masked.csv): 8a1f... (hash value)
```

**Sample encrypted output (`output/test_masked.csv.bin`):**
Binary file (not human-readable)

## Encryption (Optional)

To enable encryption/decryption, set the `ENCRYPTION_KEY` environment variable:

```bash
# Generate a key:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Then set it (e.g. in GitHub Secrets for CI):
export ENCRYPTION_KEY="your-generated-key"
```

## GitHub Actions

The workflow `.github/workflows/ci-csv-process.yml`:

- **Triggers**: Push and pull requests to `main` or `master`
- **Jobs**:
  - `process-csv` – Processes CSVs, uploads output artifacts
  - `test` – Runs pytest

## Running Tests

```bash
pytest tests/ -v
```

## Python Version Compatibility

Tested with **Python 3.8+**

## Troubleshooting / FAQ

**Q: I get an error about `ENCRYPTION_KEY` not being set.**
A: Set the `ENCRYPTION_KEY` environment variable before running encryption/decryption. See the Encryption section above for instructions.

**Q: My output files are missing or empty.**
A: Ensure your input files are in the `input/` folder and have the correct format. Check for errors in the terminal output.

**Q: How do I add new sensitive columns to mask?**
A: Edit the patterns in `src/config.py` as described in the Configuration section.

**Q: Which Python versions are supported?**
A: The project is tested with Python 3.8 and above.

## Configuration

Edit `src/config.py` to:

- Add sensitive column patterns for masking
- Change input/output paths
- Customize checksum behavior

## Contributors

This project was developed by:

- Carpio, Jhenelle O.
- Crisostomo, Selvin A.
- Maclang, Clark Danniel V.
- Pangilinan, Paul Andrei M.

BS CpE 4C
