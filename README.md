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
├── input/              # Place CSV files here
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

2. **Add CSV files** to the `input/` folder

3. **Run the pipeline**
   ```bash
   python main.py
   ```

4. **View results** in the `output/` folder

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

## Configuration

Edit `src/config.py` to:

- Add sensitive column patterns for masking
- Change input/output paths
- Customize checksum behavior
