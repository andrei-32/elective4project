"""Generate pipeline summary and visualization outputs."""

import json
import logging
from pathlib import Path

import matplotlib.pyplot as plt

from . import config

logger = logging.getLogger(__name__)


def _count_statuses(results: list[dict]) -> dict[str, int]:
    counts = {"ok": 0, "skipped": 0, "integrity_failed": 0, "error": 0}
    for result in results:
        status = result.get("status", "error")
        counts[status] = counts.get(status, 0) + 1
    return counts


def _write_status_chart(status_counts: dict[str, int], output_path: Path) -> None:
    labels = ["ok", "skipped", "integrity_failed", "error"]
    values = [status_counts.get(label, 0) for label in labels]
    colors = ["#2ca02c", "#1f77b4", "#ff7f0e", "#d62728"]

    plt.figure(figsize=(8, 4.5))
    bars = plt.bar(labels, values, color=colors)
    plt.title("CSV Pipeline Run Summary")
    plt.xlabel("Status")
    plt.ylabel("File Count")

    for bar, value in zip(bars, values):
        plt.text(
            bar.get_x() + (bar.get_width() / 2),
            value + 0.02,
            str(value),
            ha="center",
            va="bottom",
        )

    plt.tight_layout()
    plt.savefig(output_path)
    plt.close()


def write_pipeline_summary(results: list[dict]) -> tuple[Path, Path]:
    """Write summary JSON and chart image for one pipeline run."""
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    status_counts = _count_statuses(results)
    total_files = len(results)

    summary_payload = {
        "total_files": total_files,
        "status_counts": status_counts,
        "results": results,
    }

    summary_json_path = config.OUTPUT_DIR / config.SUMMARY_JSON_NAME
    summary_json_path.write_text(
        json.dumps(summary_payload, indent=2),
        encoding="utf-8",
    )

    summary_png_path = config.OUTPUT_DIR / config.SUMMARY_PNG_NAME
    _write_status_chart(status_counts, summary_png_path)

    logger.info("Wrote summary report: %s", summary_json_path)
    logger.info("Wrote summary chart: %s", summary_png_path)

    return summary_json_path, summary_png_path
