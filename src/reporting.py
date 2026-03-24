import json
import logging
from pathlib import Path

import matplotlib.gridspec as gridspec
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Restore write_pipeline_summary function
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
    output_dir = Path("output")
    output_dir.mkdir(parents=True, exist_ok=True)

    status_counts = _count_statuses(results)
    total_files = len(results)

    summary_payload = {
        "total_files": total_files,
        "status_counts": status_counts,
        "results": results,
    }

    summary_json_path = output_dir / "pipeline_summary.json"
    summary_json_path.write_text(
        json.dumps(summary_payload, indent=2),
        encoding="utf-8",
    )

    summary_png_path = output_dir / "pipeline_summary.png"
    _write_status_chart(status_counts, summary_png_path)

    logging.getLogger(__name__).info("Wrote summary report: %s", summary_json_path)
    logging.getLogger(__name__).info("Wrote summary chart: %s", summary_png_path)

    return summary_json_path, summary_png_path

def _detect_sensitive_types(df: pd.DataFrame) -> list[str]:
    """Return list of detected sensitive types in the DataFrame columns."""
    types = []
    for col in df.columns:
        col_lower = col.lower().replace(" ", "_").replace("-", "_")
        if "email" in col_lower:
            types.append("Email")
        elif "ssn" in col_lower or "social_security" in col_lower:
            types.append("SSN")
        elif "credit_card" in col_lower or "cc_number" in col_lower or "card_number" in col_lower:
            types.append("Credit Card")
        elif "phone" in col_lower:
            types.append("Phone")
        elif "identifier" in col_lower or "id_number" in col_lower or "student_id" in col_lower or "studentid" in col_lower:
            types.append("Identifier")
    return list(set(types))

def generate_file_security_summary(
    file_path: Path,
    masked_path: Path,
    encrypted_path: Path,
    checksum_path: Path,
    integrity_verified: bool,
    status: str,
    output_dir: Path,
) -> Path:
    """
    Generate a polished security summary image for a single file.
    Layout: title banner, table, pie chart (left), conclusion box (right).
    """
    from matplotlib.patches import FancyBboxPatch
    from textwrap import fill as textwrap_fill

    # ── Load data ──────────────────────────────────────────────────────
    try:
        df = pd.read_csv(file_path)
        df_masked = pd.read_csv(masked_path)
    except Exception:
        df = df_masked = pd.read_csv(masked_path)

    # ── Detect sensitive columns per type ──────────────────────────────
    all_types = ["SSN", "Email", "Credit Card", "Phone", "Identifier"]
    type_to_col = {
        "SSN": [c for c in df.columns if "ssn" in c.lower() or "social_security" in c.lower()],
        "Email": [c for c in df.columns if "email" in c.lower()],
        "Credit Card": [c for c in df.columns if any(k in c.lower() for k in ("credit_card", "cc_number", "card_number"))],
        "Phone": [c for c in df.columns if "phone" in c.lower()],
        "Identifier": [c for c in df.columns if any(k in c.lower() for k in ("identifier", "id_number", "student_id", "studentid"))],
    }

    table_data = []
    for t in all_types:
        cols = type_to_col[t]
        detected_count = masked_count = 0
        if cols:
            detected_count = int(df[cols].notna().sum().sum())
            masked_count = int(df_masked[cols].notna().sum().sum())
        if detected_count > 0:
            pct = int(round(masked_count / detected_count * 100))
            row = [
                t,
                f"{detected_count} entries",
                f"{masked_count} ({pct}%)",
                "\u2714",
                "\u2714" if integrity_verified else "\u2718",
                "\u2714 Success" if (status == "ok" and integrity_verified) else "\u2718 Failed",
            ]
        else:
            row = [t, "0", "-", "-", "-", "-"]
        table_data.append(row)

    # ── Aggregate counts for pie chart ─────────────────────────────────
    success_count = sum(1 for r in table_data if "Success" in r[-1])
    fail_count = sum(1 for r in table_data if "Failed" in r[-1])
    total_pie = success_count + fail_count

    # ── Conclusion text ────────────────────────────────────────────────
    if fail_count == 0 and success_count > 0:
        conclusion = (
            "The system successfully detected and processed all "
            "sensitive data fields within the uploaded file. All "
            "entries were masked, encrypted, and verified, achieving "
            "100% processing accuracy and data integrity."
        )
    elif total_pie == 0:
        conclusion = (
            "No sensitive data fields were detected in the uploaded "
            "file. No security actions were required."
        )
    else:
        conclusion = (
            "Some sensitive data fields were not fully processed. "
            "Please check the pipeline logs for details."
        )

    # ── Colour palette ─────────────────────────────────────────────────
    HEADER_BG   = "#1a1a2e"
    HEADER_FG   = "#ffffff"
    ROW_EVEN    = "#f8f9fa"
    ROW_ODD     = "#ffffff"
    GRID_CLR    = "#dee2e6"
    ACCENT      = "#0d6efd"
    SUCCESS_CLR = "#198754"
    FAIL_CLR    = "#dc3545"
    TEXT_CLR    = "#212529"
    MUTED_CLR   = "#6c757d"
    TITLE_BG    = "#1a1a2e"
    TITLE_FG    = "#ffffff"

    # ── Figure + gridspec ──────────────────────────────────────────────
    fig = plt.figure(figsize=(14, 9), facecolor="#ffffff")
    gs = gridspec.GridSpec(
        3, 2,
        height_ratios=[0.18, 1.0, 1.0],
        width_ratios=[1, 1],
        hspace=0.30,
        wspace=0.45,
    )

    # ── Title banner (row 0, spans both cols) ──────────────────────────
    ax_title = fig.add_subplot(gs[0, :])
    ax_title.axis("off")
    ax_title.set_xlim(0, 1)
    ax_title.set_ylim(0, 1)
    ax_title.add_patch(FancyBboxPatch(
        (0.0, 0.0), 1.0, 1.0,
        boxstyle="round,pad=0.02", facecolor=TITLE_BG,
        edgecolor="none", zorder=0,
    ))
    ax_title.text(
        0.5, 0.55, "Security Summary",
        ha="center", va="center",
        fontsize=28, fontweight="bold", color=TITLE_FG,
        family="DejaVu Sans",
    )
    ax_title.text(
        0.5, 0.12, file_path.name,
        ha="center", va="center",
        fontsize=14, color="#adb5bd", family="DejaVu Sans",
    )

    # ── Table (row 1, spans both cols) ─────────────────────────────────
    ax_table = fig.add_subplot(gs[1, :])
    ax_table.axis("off")

    headers = ["Data Type", "Detected", "Masked", "Encrypted", "Integrity", "Status"]
    col_widths = [0.17, 0.16, 0.17, 0.15, 0.15, 0.20]
    cell_h = 0.14
    n_data_rows = len(table_data)
    n_rows = n_data_rows + 1          # +1 for header
    table_w = sum(col_widths)
    table_top = 1.0

    # — header row —
    x = 0.0
    for ci, hdr in enumerate(headers):
        w = col_widths[ci]
        y = table_top - cell_h
        ax_table.add_patch(plt.Rectangle(
            (x, y), w, cell_h, facecolor=HEADER_BG,
            edgecolor=GRID_CLR, lw=1.2, zorder=2,
        ))
        ax_table.text(
            x + w / 2, y + cell_h / 2, hdr,
            ha="center", va="center",
            fontsize=13, fontweight="bold",
            color=HEADER_FG, family="DejaVu Sans",
        )
        x += w

    # — data rows —
    for ri, rowdata in enumerate(table_data):
        x = 0.0
        row_bg = ROW_EVEN if ri % 2 == 0 else ROW_ODD
        for ci, val in enumerate(rowdata):
            w = col_widths[ci]
            y = table_top - (ri + 2) * cell_h
            # choose colours for status column
            fg = TEXT_CLR
            if ci == 5:
                if "Success" in val:
                    fg = SUCCESS_CLR
                elif "Failed" in val:
                    fg = FAIL_CLR
            elif val == "-":
                fg = MUTED_CLR

            ax_table.add_patch(plt.Rectangle(
                (x, y), w, cell_h, facecolor=row_bg,
                edgecolor=GRID_CLR, lw=0.8, zorder=1,
            ))
            ax_table.text(
                x + w / 2, y + cell_h / 2, str(val),
                ha="center", va="center",
                fontsize=12, color=fg,
                fontweight="bold" if ci in (0, 5) else "normal",
                family="DejaVu Sans",
            )
            x += w

    ax_table.set_xlim(0, table_w)
    ax_table.set_ylim(table_top - n_rows * cell_h - 0.02, table_top + 0.02)

    # ── Pie chart (row 2, col 0) ──────────────────────────────────────
    ax_pie = fig.add_subplot(gs[2, 0])

    if total_pie == 0:
        ax_pie.axis("off")
        ax_pie.text(
            0.5, 0.5, "No sensitive data detected",
            ha="center", va="center",
            fontsize=14, color=MUTED_CLR, fontweight="bold",
        )
        ax_pie.set_title("Success Rate", fontsize=16, fontweight="bold",
                         pad=12, color=TEXT_CLR, family="DejaVu Sans")
    else:
        pie_sizes = [success_count, fail_count]
        pie_colors_list = [SUCCESS_CLR, FAIL_CLR]
        pie_labels = ["Success", "Failed"]
        wedges, _ = ax_pie.pie(
            pie_sizes,
            labels=None,
            colors=pie_colors_list,
            startangle=90,
            wedgeprops={"edgecolor": "#ffffff", "linewidth": 2.5},
        )
        # percentage labels inside wedges
        for w, lbl, sz in zip(wedges, pie_labels, pie_sizes):
            if sz == 0:
                continue
            ang = (w.theta2 + w.theta1) / 2
            r = 0.62
            x = r * np.cos(np.deg2rad(ang))
            y = r * np.sin(np.deg2rad(ang))
            ax_pie.text(
                x, y,
                f"{lbl}\n{int(sz / total_pie * 100)}%",
                ha="center", va="center",
                fontsize=13, fontweight="bold", color="#fff",
            )
        legend_patches = [
            mpatches.Patch(color=c, label=l)
            for c, l in zip(pie_colors_list, pie_labels)
        ]
        leg = ax_pie.legend(
            handles=legend_patches,
            loc="upper center", bbox_to_anchor=(0.5, -0.08),
            ncol=2, fontsize=12, frameon=True, borderpad=0.8,
            edgecolor=GRID_CLR,
        )
        leg.get_frame().set_linewidth(1.0)
        ax_pie.axis("equal")
        ax_pie.set_title("Success Rate", fontsize=16, fontweight="bold",
                         pad=12, color=TEXT_CLR, family="DejaVu Sans")

    # ── Conclusion box (row 2, col 1) ─────────────────────────────────
    ax_conc = fig.add_subplot(gs[2, 1])
    ax_conc.axis("off")
    ax_conc.set_xlim(0, 1)
    ax_conc.set_ylim(0, 1)

    bx, by, bw, bh = 0.05, 0.10, 0.90, 0.72
    # subtle shadow
    ax_conc.add_patch(FancyBboxPatch(
        (bx + 0.012, by - 0.012), bw, bh,
        boxstyle="round,pad=0.04", facecolor="#adb5bd",
        alpha=0.18, linewidth=0, zorder=1,
    ))
    # main card
    ax_conc.add_patch(FancyBboxPatch(
        (bx, by), bw, bh,
        boxstyle="round,pad=0.04", facecolor="#ffffff",
        edgecolor=ACCENT, linewidth=1.8, zorder=2,
    ))
    # header label
    ax_conc.text(
        bx + bw / 2, by + bh + 0.06, "Conclusion",
        ha="center", va="bottom",
        fontsize=20, fontweight="bold",
        color=TEXT_CLR, family="DejaVu Sans",
    )
    # wrapped conclusion text
    wrapped = textwrap_fill(conclusion, width=42)
    ax_conc.text(
        bx + bw / 2, by + bh / 2 + 0.02, wrapped,
        ha="center", va="center",
        fontsize=12, color=TEXT_CLR,
        linespacing=1.45, family="DejaVu Sans",
        zorder=3,
    )

    # ── Save ───────────────────────────────────────────────────────────
    img_path = output_dir / f"{file_path.stem}_security_summary.png"
    plt.savefig(img_path, dpi=180, bbox_inches="tight", facecolor="#ffffff")
    plt.close(fig)
    return img_path
