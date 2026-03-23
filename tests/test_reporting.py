"""Tests for pipeline summary reporting."""

import json

from src.reporting import write_pipeline_summary


def test_write_pipeline_summary_creates_json_and_chart(input_output_dirs):
    """Summary artifacts should be generated in output directory."""
    _, output_dir = input_output_dirs

    results = [
        {"file": "a.csv", "status": "ok", "outputs": ["a_masked.csv"]},
        {"file": "b.csv", "status": "error", "outputs": [], "error": "failed"},
    ]

    json_path, png_path = write_pipeline_summary(results)

    assert json_path.exists()
    assert png_path.exists()
    assert png_path.stat().st_size > 0

    summary = json.loads(json_path.read_text(encoding="utf-8"))
    assert summary["total_files"] == 2
    assert summary["status_counts"]["ok"] == 1
    assert summary["status_counts"]["error"] == 1
    assert len(summary["results"]) == 2
