"""Download an external CSV file into input folder."""

import argparse
import logging
from pathlib import Path
from urllib.request import Request, urlopen

from . import config

DEFAULT_DATASET_URL = "https://raw.githubusercontent.com/mwaskom/seaborn-data/master/tips.csv"

logger = logging.getLogger(__name__)


def download_csv(url: str = DEFAULT_DATASET_URL, output_file: str | Path | None = None) -> Path:
    """Download a CSV file from URL and save into input directory."""
    config.INPUT_DIR.mkdir(parents=True, exist_ok=True)

    destination = Path(output_file) if output_file else (config.INPUT_DIR / "external_dataset.csv")
    destination.parent.mkdir(parents=True, exist_ok=True)

    request = Request(url, headers={"User-Agent": "csv-pipeline/1.0"})
    with urlopen(request, timeout=30) as response:
        content = response.read()

    if not content:
        raise ValueError(f"Downloaded file is empty from URL: {url}")

    destination.write_bytes(content)
    logger.info("Downloaded CSV from %s to %s", url, destination)
    return destination


def main() -> int:
    parser = argparse.ArgumentParser(description="Download an external CSV file.")
    parser.add_argument("--url", default=DEFAULT_DATASET_URL, help="CSV URL to download")
    parser.add_argument("--output", default=str(config.INPUT_DIR / "external_dataset.csv"), help="Output file path")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO)

    try:
        download_csv(url=args.url, output_file=args.output)
        return 0
    except Exception:
        logger.exception("Failed to download CSV dataset")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
