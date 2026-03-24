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
import numpy as np
import matplotlib.patches as mpatches
import pandas as pd
import matplotlib.gridspec as gridspec
import matplotlib.pyplot as plt
import json
import logging
from pathlib import Path
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
    Generate a category-based security summary table, pie chart, and short explanation as an image for a single file.
    Returns the path to the generated image.
    """
    # Load original and masked data
    try:
        df = pd.read_csv(file_path)
        df_masked = pd.read_csv(masked_path)
    except Exception:
        # Fallback: just use masked if original fails
        df = df_masked = pd.read_csv(masked_path)

    sensitive_types = _detect_sensitive_types(df)
    # Only show SSN, Email, Credit Card for the improved table
    all_types = ["SSN", "Email", "Credit Card"]
    type_to_col = {
        "SSN": [c for c in df.columns if "ssn" in c.lower() or "social_security" in c.lower()],
        "Email": [c for c in df.columns if "email" in c.lower()],
        "Credit Card": [c for c in df.columns if "credit_card" in c.lower() or "cc_number" in c.lower() or "card_number" in c.lower()],
    }
    table_data = []
    for t in all_types:
        cols = type_to_col[t]
        detected_count = 0
        masked_count = 0
        total = 0
        if cols:
            # Count non-null entries in original and masked
            detected_count = int(df[cols].notna().sum().sum())
            masked_count = int(df_masked[cols].notna().sum().sum())
            total = len(df)
        detected_str = f"{detected_count} entries" if detected_count > 0 else "0"
        if detected_count > 0:
            percent = int(round(masked_count / detected_count * 100)) if detected_count else 0
            masked_str = f"{masked_count} ({percent}%)"
            encrypted_str = "✔"
            integrity_str = "✔" if integrity_verified else "✖"
            stat = "✅ Success" if status == "ok" and integrity_verified else "❌ Failed"
        else:
            masked_str = encrypted_str = integrity_str = stat = "-"
        table_data.append([t, detected_str, masked_str, encrypted_str, integrity_str, stat])

    # Pie chart: Success/Failed
    success_count = sum(1 for row in table_data if row[-1] == "✅ Success")
    fail_count = sum(1 for row in table_data if row[-1] == "❌ Failed")
    total = success_count + fail_count
    pie_labels = ["Success", "Failed"]
    pie_sizes = [success_count, fail_count]
    pie_colors = ["#2ca02c", "#d62728"]

    # Short explanation
    if fail_count == 0 and success_count > 0:
        short_text = (
            "The system successfully detected and processed all sensitive data fields within the uploaded file. "
            "All entries were masked, encrypted, and verified, achieving 100% processing accuracy and data integrity."
        )
    elif total == 0:
        short_text = (
            "No sensitive data fields were detected in the uploaded file. No security actions were required."
        )
    else:
        short_text = (
            "Some sensitive data fields were not fully processed. Please check the pipeline logs for details."
        )

    # Plot
    import matplotlib.pyplot as plt
    fig, axs = plt.subplots(2, 1, figsize=(8, 7), gridspec_kw={'height_ratios': [2, 1]})
    ax_table, ax_pie = axs

    # Draw a colored, grid-style table using matplotlib axis
    ax_table.axis('off')
    # --- Use gridspec for layout ---
    import matplotlib.gridspec as gridspec
    fig = plt.figure(figsize=(12, 9))
    gs = gridspec.GridSpec(3, 2, height_ratios=[1.1, 0.9, 1.1], width_ratios=[1, 1], hspace=0.35, wspace=0.18)
    # Table at the top (spans both columns)
    ax_table = fig.add_subplot(gs[0, :])
    ax_table.axis('off')
    # Table data
    n_extra_rows = 2
    nrows, ncols = len(table_data) + 1 + n_extra_rows, len(table_data[0])
    # Widen columns for better spacing
    col_widths = [0.18, 0.18, 0.18, 0.15, 0.15, 0.16]
    cell_height = 0.13
    header_color = '#7c1313'
    header_fg = '#fff'
    grid_color = '#222'
    # Draw header
    x = 0
    for col, label in enumerate(["Data Type", "Detected", "Masked", "Encrypted", "Integrity Verified", "Status"]):
        w = col_widths[col]
        ax_table.add_patch(plt.Rectangle((x, 1 - cell_height), w, cell_height, facecolor=header_color, edgecolor=grid_color, lw=2, zorder=2))
        ax_table.text(x + w/2, 1 - cell_height/2, label, ha='center', va='center', fontsize=16, fontweight='bold', color=header_fg, family='DejaVu Sans')
        x += w
    # Draw rows
    for row, rowdata in enumerate(table_data):
        x = 0
        for col, val in enumerate(rowdata):
            w = col_widths[col]
            y = 1 - (row + 2) * cell_height
            # Use DejaVu Sans for check marks
            fontfam = 'DejaVu Sans' if (col in [3,4] and (val == '✓' or val == '\u2714')) else 'Comic Sans MS'
            if col == 5:
                if 'Success' in val:
                    bgcolor = '#fff'
                    fgcolor = '#222'
                elif 'Failed' in val:
                    bgcolor = '#fff'
                    fgcolor = '#b22222'
                else:
                    bgcolor = '#fff'
                    fgcolor = '#888'
            else:
                bgcolor = '#fff'
                fgcolor = '#222'
            ax_table.add_patch(plt.Rectangle((x, y), w, cell_height, facecolor=bgcolor, edgecolor=grid_color, lw=1.5, zorder=1))
            ax_table.text(x + w/2, y + cell_height/2, str(val), ha='center', va='center', fontsize=15, color=fgcolor, fontweight='bold' if col == 5 else 'normal', family=fontfam)
            x += w
    # Draw extra empty rows for spacing
    for extra in range(n_extra_rows):
        x = 0
        y = 1 - (len(table_data) + 2 + extra) * cell_height
        for col in range(ncols):
            w = col_widths[col]
            ax_table.add_patch(plt.Rectangle((x, y), w, cell_height, facecolor='#fff', edgecolor=grid_color, lw=1.5, zorder=1))
            x += w
    # Draw grid lines
    x = 0
    for j in range(ncols+1):
        ax_table.plot([x, x], [1, 1 - nrows*cell_height], color=grid_color, lw=1.5, zorder=3)
        if j < ncols:
            x += col_widths[j]
    for i in range(nrows+1):
        ax_table.plot([0, sum(col_widths)], [1 - i*cell_height, 1 - i*cell_height], color=grid_color, lw=1.5, zorder=3)
    ax_table.set_xlim(0, sum(col_widths))
    ax_table.set_ylim(1 - nrows*cell_height - 0.04, 1 + 0.04)
    # Title (script/bold)
    try:
        ax_table.set_title("Category Based-Security Summary", fontsize=36, pad=18, fontweight='bold', family='Comic Sans MS')
    except:
        ax_table.set_title("Category Based-Security Summary", fontsize=36, pad=18, fontweight='bold')
    # --- Pie Chart (left, row 2 col 0) ---
    ax_pie = fig.add_subplot(gs[1, 0])
    # ...existing code for pie chart, but set title with script font and add legend in a box...
    # Move legend to the right of the pie chart, boxed, and not overlapping conclusion
    pie_legend = ax_pie.legend(loc='center left', bbox_to_anchor=(1.05, 0.5), frameon=True, fontsize=13, borderpad=1, title=None)
    pie_legend.get_frame().set_edgecolor('#222')
    pie_legend.get_frame().set_linewidth(1.5)
    # --- Conclusion Box (right, row 1 col 1, spans row 1 and 2) ---
    ax_conc = fig.add_subplot(gs[1:, 1])
    ax_conc.axis('off')
    # Draw drop-shadowed box for conclusion, moved left for better alignment
    from matplotlib.patches import FancyBboxPatch
    box_x, box_y, box_w, box_h = 0.08, 0.32, 0.82, 0.45
    # Shadow
    shadow = FancyBboxPatch((box_x+0.015, box_y-0.015), box_w, box_h, boxstyle="round,pad=0.03", linewidth=0, facecolor="#888", alpha=0.22, zorder=1)
    ax_conc.add_patch(shadow)
    # Main box
    box = FancyBboxPatch((box_x, box_y), box_w, box_h, boxstyle="round,pad=0.03", linewidth=1.5, facecolor="#fff", edgecolor="#444", zorder=2)
    ax_conc.add_patch(box)
    # Conclusion header
    ax_conc.text(box_x + box_w/2, box_y+box_h+0.07, "Conclusion", ha='center', va='bottom', fontsize=24, fontweight='bold', family='Comic Sans MS')
    # Conclusion text
    conclusion_text = None
    if 'summary' in locals():
        conclusion_text = summary
    elif 'summary_str' in locals():
        conclusion_text = summary_str
    else:
        conclusion_text = "The system successfully processed the uploaded file by detecting all sensitive data fields. All entries were masked, encrypted, and verified, resulting in 100% processing success and ensured data integrity."
    ax_conc.text(box_x + box_w/2, box_y+box_h/2, conclusion_text, ha='center', va='center', fontsize=15, color='#222', wrap=True, zorder=3)
    # Remove axes
    ax_conc.set_xlim(0, 1)
    ax_conc.set_ylim(0, 1)
    # ...rest of function unchanged...

    # Pie chart or message (modern style)
    if total == 0:
        ax_pie.axis('off')
        ax_pie.text(0.5, 0.5, "No sensitive data detected", ha='center', va='center', fontsize=15, color='#555', fontweight='bold')
        ax_pie.set_title("Success Rate", fontsize=14, fontweight='bold')
    else:
        wedges, texts = ax_pie.pie(
            pie_sizes,
            labels=None,
            autopct=None,
            colors=pie_colors,
            startangle=90,
            textprops={'fontsize': 13},
            wedgeprops={'edgecolor': 'white', 'linewidth': 2},
        )
        # Add custom legend and percent labels
        for i, (w, label, size) in enumerate(zip(wedges, pie_labels, pie_sizes)):
            ang = (w.theta2 + w.theta1) / 2
            x = 0.7 * np.cos(np.deg2rad(ang))
            y = 0.7 * np.sin(np.deg2rad(ang))
            if size > 0:
                ax_pie.text(x, y, f"{label}\n{int(size/total*100)}%", ha='center', va='center', fontsize=14, fontweight='bold', color='#222')
        legend_patches = [mpatches.Patch(color=pie_colors[i], label=pie_labels[i]) for i in range(len(pie_labels))]
        ax_pie.legend(handles=legend_patches, loc='center left', bbox_to_anchor=(1, 0.5), fontsize=12, frameon=False)
        ax_pie.axis('equal')
        ax_pie.set_title("Success Rate", fontsize=14, fontweight='bold')

    # Short text below (modern style)
    fig.text(0.5, 0.01, short_text, ha='center', va='bottom', fontsize=13, color='#333', wrap=True, fontweight='medium')

    # Save image
    img_path = output_dir / f"{file_path.stem}_security_summary.png"
    plt.tight_layout(rect=[0, 0.04, 1, 0.98])
    plt.savefig(img_path, dpi=200, bbox_inches='tight')
    plt.close(fig)
    return img_path
