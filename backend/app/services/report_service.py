from __future__ import annotations

import csv
import html
import json
import re
import tempfile
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from statistics import mean
from typing import Any
from uuid import uuid4

from app.config import PROJECT_ROOT, settings
from app.db.repositories.files import UploadedFileRepository


GROUP_COLUMN_ALIASES = {
    "floor": "floor",
    "floor_name": "floor",
    "floor_no": "floor",
    "floor number": "floor",
    "level": "floor",
    "storey": "floor",
}


@dataclass
class AttachmentDataset:
    filename: str
    columns: list[str]
    rows: list[dict[str, str]]


class ReportService:
    def __init__(self) -> None:
        self.root = Path(settings.file_storage_path)
        self.file_repository = UploadedFileRepository()

    def build_report(
        self,
        workspace_id: str,
        attachments: list[str],
        parameters: dict[str, Any],
        user_input: str,
    ) -> dict[str, Any]:
        dataset = self._load_dataset(workspace_id, attachments)
        report_title = self._build_title(parameters, dataset)
        generated_at = datetime.now(UTC).strftime("%d %b %Y %H:%M UTC")

        if dataset is None:
            payload = self._fallback_report(report_title, workspace_id, parameters, user_input, generated_at)
        else:
            payload = self._dataset_report(report_title, workspace_id, parameters, user_input, generated_at, dataset)

        files = self._export_report_files(workspace_id, payload)
        payload["report_files"] = files
        payload["pdf_generated"] = "pdf" in files
        return payload

    def _build_title(self, parameters: dict[str, Any], dataset: AttachmentDataset | None) -> str:
        audience = str(parameters.get("audience", "management")).replace("_", " ").title()
        if dataset:
            return f"{dataset.filename} Analysis Report for {audience}"
        return "Dynamic Business Report"

    def _load_dataset(self, workspace_id: str, attachments: list[str]) -> AttachmentDataset | None:
        if not attachments:
            return None

        attachment_id = attachments[0]
        uploaded = self.file_repository.get_by_id(attachment_id, workspace_id)
        if uploaded is None:
            return None

        path = Path(uploaded.storage_path)
        if not path.exists():
            return None

        suffix = path.suffix.lower()
        if suffix not in {".csv", ".tsv"}:
            return None

        delimiter = "\t" if suffix == ".tsv" else ","
        with path.open("r", encoding="utf-8", errors="ignore", newline="") as handle:
            reader = csv.DictReader(handle, delimiter=delimiter)
            rows = []
            for raw_row in reader:
                cleaned = {str(key or "").strip(): str(value or "").strip() for key, value in raw_row.items()}
                if any(value for value in cleaned.values()):
                    rows.append(cleaned)

        if not rows:
            return AttachmentDataset(filename=uploaded.filename, columns=reader.fieldnames or [], rows=[])

        columns = [str(column or "").strip() for column in rows[0].keys()]
        return AttachmentDataset(filename=uploaded.filename, columns=columns, rows=rows)

    def _dataset_report(
        self,
        title: str,
        workspace_id: str,
        parameters: dict[str, Any],
        user_input: str,
        generated_at: str,
        dataset: AttachmentDataset,
    ) -> dict[str, Any]:
        numeric_columns = self._numeric_columns(dataset.rows)
        group_column = self._detect_group_column(dataset.columns, parameters)
        totals = self._totals(dataset.rows, numeric_columns)
        averages = self._averages(dataset.rows, numeric_columns)
        floor_breakdown = self._group_breakdown(dataset.rows, group_column, numeric_columns)

        highlights = self._build_highlights(dataset, totals, averages, group_column, floor_breakdown)
        recommendations = self._build_recommendations(group_column, floor_breakdown, numeric_columns)
        report_text = self._compose_plain_report(
            title=title,
            workspace_id=workspace_id,
            generated_at=generated_at,
            user_input=user_input,
            dataset=dataset,
            group_column=group_column,
            totals=totals,
            averages=averages,
            floor_breakdown=floor_breakdown,
            highlights=highlights,
            recommendations=recommendations,
        )

        return {
            "status": "success",
            "report_title": title,
            "report": report_text,
            "highlights": highlights,
            "recommended_actions": recommendations,
            "source_filename": dataset.filename,
            "source_columns": dataset.columns,
            "row_count": len(dataset.rows),
            "group_by": group_column,
            "totals": totals,
            "averages": averages,
            "floor_breakdown": floor_breakdown,
            "generated_at": generated_at,
        }

    def _fallback_report(
        self,
        title: str,
        workspace_id: str,
        parameters: dict[str, Any],
        user_input: str,
        generated_at: str,
    ) -> dict[str, Any]:
        period = str(parameters.get("period", "custom")).title()
        audience = str(parameters.get("audience", "management")).replace("_", " ").title()
        summary = [
            "No structured CSV or TSV file was attached, so I created a narrative report shell.",
            "Attach a floor-wise CSV file to generate exact totals, averages, and section-by-section calculations.",
        ]
        recommendations = [
            "Upload a CSV or TSV file with columns like Floor, Area, Quantity, Cost, Revenue, or Load.",
            "Ask for floor-wise calculations to get grouped totals and averages automatically.",
            "Use the generated HTML report immediately, and PDF will be created if the PDF package is installed.",
        ]
        report_text = "\n".join(
            [
                title,
                "",
                f"Workspace: {workspace_id}",
                f"Generated: {generated_at}",
                f"Audience: {audience}",
                f"Period: {period}",
                "",
                "Summary:",
                *[f"- {line}" for line in summary],
            ]
        )
        return {
            "status": "success",
            "report_title": title,
            "report": report_text,
            "highlights": summary,
            "recommended_actions": recommendations,
            "source_filename": "",
            "source_columns": [],
            "row_count": 0,
            "group_by": None,
            "totals": {},
            "averages": {},
            "floor_breakdown": [],
            "generated_at": generated_at,
            "requested_prompt": user_input,
        }

    def _numeric_columns(self, rows: list[dict[str, str]]) -> list[str]:
        numeric_columns: list[str] = []
        if not rows:
            return numeric_columns
        for column in rows[0].keys():
            values = [self._to_float(row.get(column, "")) for row in rows]
            numeric_values = [value for value in values if value is not None]
            if numeric_values and len(numeric_values) >= max(1, len(rows) // 2):
                numeric_columns.append(column)
        return numeric_columns

    def _detect_group_column(self, columns: list[str], parameters: dict[str, Any]) -> str | None:
        requested = str(parameters.get("group_by", "")).strip().lower()
        normalized_columns = {column.lower(): column for column in columns}

        if requested:
            for key, value in normalized_columns.items():
                if requested == key:
                    return value
                if GROUP_COLUMN_ALIASES.get(key) == requested:
                    return value

        for column in columns:
            normalized = column.lower().strip()
            if normalized in GROUP_COLUMN_ALIASES:
                return column
        return None

    def _totals(self, rows: list[dict[str, str]], numeric_columns: list[str]) -> dict[str, float]:
        return {
            column: round(sum(self._to_float(row.get(column, "")) or 0.0 for row in rows), 2)
            for column in numeric_columns
        }

    def _averages(self, rows: list[dict[str, str]], numeric_columns: list[str]) -> dict[str, float]:
        averages: dict[str, float] = {}
        for column in numeric_columns:
            values = [self._to_float(row.get(column, "")) for row in rows]
            numeric_values = [value for value in values if value is not None]
            if numeric_values:
                averages[column] = round(mean(numeric_values), 2)
        return averages

    def _group_breakdown(
        self,
        rows: list[dict[str, str]],
        group_column: str | None,
        numeric_columns: list[str],
    ) -> list[dict[str, Any]]:
        if not group_column:
            return []

        grouped: dict[str, list[dict[str, str]]] = {}
        for row in rows:
            group = row.get(group_column, "").strip() or "Unspecified"
            grouped.setdefault(group, []).append(row)

        breakdown: list[dict[str, Any]] = []
        for group_name, group_rows in sorted(grouped.items(), key=lambda item: item[0].lower()):
            totals = self._totals(group_rows, numeric_columns)
            averages = self._averages(group_rows, numeric_columns)
            breakdown.append(
                {
                    "group": group_name,
                    "row_count": len(group_rows),
                    "totals": totals,
                    "averages": averages,
                }
            )
        return breakdown

    def _build_highlights(
        self,
        dataset: AttachmentDataset,
        totals: dict[str, float],
        averages: dict[str, float],
        group_column: str | None,
        breakdown: list[dict[str, Any]],
    ) -> list[str]:
        highlights = [f"Processed {len(dataset.rows)} rows from {dataset.filename}."]
        if totals:
            key_total = max(totals.items(), key=lambda item: abs(item[1]))
            highlights.append(f"Highest aggregate metric is {key_total[0]} with a total of {key_total[1]:,.2f}.")
        if averages:
            key_avg = max(averages.items(), key=lambda item: abs(item[1]))
            highlights.append(f"Highest average metric is {key_avg[0]} at {key_avg[1]:,.2f}.")
        if group_column and breakdown:
            ranked = self._best_group_entry(breakdown)
            if ranked:
                highlights.append(
                    f"Top {group_column} segment is {ranked['group']} based on the strongest total metric."
                )
        return highlights

    def _build_recommendations(
        self,
        group_column: str | None,
        breakdown: list[dict[str, Any]],
        numeric_columns: list[str],
    ) -> list[str]:
        recommendations = [
            "Review the highlighted metrics before sharing the report outside the workspace.",
            "Use the HTML report for quick review and the PDF export for formal sharing.",
        ]
        if group_column and breakdown:
            recommendations.append(f"Track {group_column}-wise totals regularly to catch weak segments early.")
        if len(numeric_columns) >= 2:
            recommendations.append(
                f"Compare {numeric_columns[0]} against {numeric_columns[1]} to identify efficiency gaps."
            )
        return recommendations[:4]

    def _compose_plain_report(
        self,
        *,
        title: str,
        workspace_id: str,
        generated_at: str,
        user_input: str,
        dataset: AttachmentDataset,
        group_column: str | None,
        totals: dict[str, float],
        averages: dict[str, float],
        floor_breakdown: list[dict[str, Any]],
        highlights: list[str],
        recommendations: list[str],
    ) -> str:
        lines = [
            title,
            "",
            f"Workspace: {workspace_id}",
            f"Generated: {generated_at}",
            f"Source file: {dataset.filename}",
            f"Rows analyzed: {len(dataset.rows)}",
            f"Columns: {', '.join(dataset.columns) or 'N/A'}",
            f"Requested task: {user_input}",
            "",
            "Highlights:",
            *[f"- {item}" for item in highlights],
            "",
            "Totals:",
        ]
        if totals:
            lines.extend(f"- {key}: {value:,.2f}" for key, value in totals.items())
        else:
            lines.append("- No numeric columns detected.")

        lines.extend(["", "Averages:"])
        if averages:
            lines.extend(f"- {key}: {value:,.2f}" for key, value in averages.items())
        else:
            lines.append("- No numeric averages available.")

        if group_column and floor_breakdown:
            lines.extend(["", f"{group_column.title()} Breakdown:"])
            for item in floor_breakdown:
                totals_text = ", ".join(f"{key}={value:,.2f}" for key, value in item["totals"].items()) or "no totals"
                lines.append(f"- {item['group']}: {item['row_count']} rows, {totals_text}")

        lines.extend(["", "Recommended Actions:"])
        lines.extend(f"- {item}" for item in recommendations)
        return "\n".join(lines)

    def _export_report_files(self, workspace_id: str, payload: dict[str, Any]) -> dict[str, str]:
        report_dir = self._resolve_report_dir(workspace_id)
        slug = self._slugify(str(payload.get("report_title", "report")))
        token = uuid4().hex[:8]
        stem = f"{slug}-{token}"

        json_path = report_dir / f"{stem}.json"
        txt_path = report_dir / f"{stem}.txt"
        html_path = report_dir / f"{stem}.html"

        json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        txt_path.write_text(str(payload.get("report", "")), encoding="utf-8")
        html_path.write_text(self._render_html(payload), encoding="utf-8")

        files = {
            "json": str(json_path),
            "text": str(txt_path),
            "html": str(html_path),
        }

        pdf_path = report_dir / f"{stem}.pdf"
        if self._write_pdf(payload, pdf_path):
            files["pdf"] = str(pdf_path)
        return files

    def _resolve_report_dir(self, workspace_id: str) -> Path:
        candidates = [
            self.root / workspace_id / "reports",
            PROJECT_ROOT / ".sikha-data" / "reports" / workspace_id,
            Path(tempfile.gettempdir()) / "sikha-reports" / workspace_id,
        ]
        for candidate in candidates:
            try:
                candidate.mkdir(parents=True, exist_ok=True)
                return candidate
            except PermissionError:
                continue
        raise PermissionError("Unable to create a writable report export directory.")

    def _render_html(self, payload: dict[str, Any]) -> str:
        highlights = "".join(f"<li>{html.escape(item)}</li>" for item in payload.get("highlights", []))
        actions = "".join(f"<li>{html.escape(item)}</li>" for item in payload.get("recommended_actions", []))
        totals_rows = "".join(
            f"<tr><td>{html.escape(str(key))}</td><td>{value:,.2f}</td></tr>"
            for key, value in payload.get("totals", {}).items()
        )
        avg_rows = "".join(
            f"<tr><td>{html.escape(str(key))}</td><td>{value:,.2f}</td></tr>"
            for key, value in payload.get("averages", {}).items()
        )
        breakdown_rows = "".join(
            "<tr>"
            f"<td>{html.escape(str(item.get('group', '')))}</td>"
            f"<td>{int(item.get('row_count', 0))}</td>"
            f"<td>{html.escape(', '.join(f'{key}={value:,.2f}' for key, value in item.get('totals', {}).items()) or 'No totals')}</td>"
            "</tr>"
            for item in payload.get("floor_breakdown", [])
        )
        source_columns = ", ".join(str(column) for column in payload.get("source_columns", [])) or "N/A"
        report_body = html.escape(str(payload.get("report", ""))).replace("\n", "<br>")

        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>{html.escape(str(payload.get("report_title", "Report")))}</title>
  <style>
    body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #f4f1ea; color: #182026; margin: 0; padding: 32px; }}
    .sheet {{ max-width: 980px; margin: 0 auto; background: #fffdf8; border-radius: 22px; padding: 32px; box-shadow: 0 18px 55px rgba(40, 34, 24, 0.12); }}
    .hero {{ padding: 24px; border-radius: 18px; background: linear-gradient(135deg, #17333d, #2d5b62); color: white; }}
    .hero h1 {{ margin: 0 0 10px; font-size: 32px; }}
    .meta {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 12px; margin-top: 18px; }}
    .chip {{ background: rgba(255,255,255,0.13); border-radius: 14px; padding: 12px 14px; }}
    .grid {{ display: grid; grid-template-columns: 1.2fr 0.8fr; gap: 22px; margin-top: 24px; }}
    .card {{ background: #f9f6ef; border: 1px solid #ece3d2; border-radius: 18px; padding: 20px; }}
    table {{ width: 100%; border-collapse: collapse; margin-top: 12px; }}
    th, td {{ text-align: left; padding: 10px 12px; border-bottom: 1px solid #eadfcd; }}
    th {{ color: #4c5a5f; font-size: 13px; text-transform: uppercase; letter-spacing: 0.04em; }}
    ul {{ margin: 10px 0 0 18px; padding: 0; }}
    .full {{ margin-top: 24px; }}
    .mono {{ font-family: Consolas, monospace; white-space: pre-wrap; line-height: 1.5; }}
  </style>
</head>
<body>
  <div class="sheet">
    <section class="hero">
      <h1>{html.escape(str(payload.get("report_title", "Dynamic Report")))}</h1>
      <div>{html.escape(str(payload.get("source_filename", "") or "Generated without attachment"))}</div>
      <div class="meta">
        <div class="chip"><strong>Generated</strong><br>{html.escape(str(payload.get("generated_at", "")))}</div>
        <div class="chip"><strong>Rows analyzed</strong><br>{int(payload.get("row_count", 0))}</div>
        <div class="chip"><strong>Grouped by</strong><br>{html.escape(str(payload.get("group_by") or "None"))}</div>
        <div class="chip"><strong>Columns</strong><br>{html.escape(source_columns)}</div>
      </div>
    </section>
    <section class="grid">
      <div class="card">
        <h2>Highlights</h2>
        <ul>{highlights or '<li>No highlights available.</li>'}</ul>
      </div>
      <div class="card">
        <h2>Recommended Actions</h2>
        <ul>{actions or '<li>No actions available.</li>'}</ul>
      </div>
    </section>
    <section class="grid">
      <div class="card">
        <h2>Totals</h2>
        <table>
          <thead><tr><th>Metric</th><th>Total</th></tr></thead>
          <tbody>{totals_rows or '<tr><td colspan="2">No numeric totals found.</td></tr>'}</tbody>
        </table>
      </div>
      <div class="card">
        <h2>Averages</h2>
        <table>
          <thead><tr><th>Metric</th><th>Average</th></tr></thead>
          <tbody>{avg_rows or '<tr><td colspan="2">No numeric averages found.</td></tr>'}</tbody>
        </table>
      </div>
    </section>
    <section class="card full">
      <h2>Floor or Group Breakdown</h2>
      <table>
        <thead><tr><th>Group</th><th>Rows</th><th>Totals</th></tr></thead>
        <tbody>{breakdown_rows or '<tr><td colspan="3">No group breakdown available.</td></tr>'}</tbody>
      </table>
    </section>
    <section class="card full">
      <h2>Full Report</h2>
      <div class="mono">{report_body}</div>
    </section>
  </div>
</body>
</html>
"""

    def _write_pdf(self, payload: dict[str, Any], pdf_path: Path) -> bool:
        try:
            from reportlab.lib import colors
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
            from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        except ImportError:
            return False

        document = SimpleDocTemplate(str(pdf_path), pagesize=A4, leftMargin=32, rightMargin=32, topMargin=28, bottomMargin=28)
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        title_style.textColor = colors.HexColor("#17333d")
        sub_style = ParagraphStyle("Sub", parent=styles["BodyText"], textColor=colors.HexColor("#50616a"), leading=16)
        heading_style = styles["Heading2"]
        heading_style.textColor = colors.HexColor("#214652")

        story: list[Any] = [
            Paragraph(html.escape(str(payload.get("report_title", "Dynamic Report"))), title_style),
            Spacer(1, 6),
            Paragraph(f"Generated: {html.escape(str(payload.get('generated_at', '')))}", sub_style),
            Paragraph(f"Source: {html.escape(str(payload.get('source_filename', '') or 'No structured file'))}", sub_style),
            Spacer(1, 14),
            Paragraph("Highlights", heading_style),
        ]
        for item in payload.get("highlights", []):
            story.append(Paragraph(f"• {html.escape(str(item))}", styles["BodyText"]))
        story.append(Spacer(1, 12))

        totals = payload.get("totals", {})
        story.append(Paragraph("Totals", heading_style))
        story.append(self._pdf_table([["Metric", "Total"], *[[str(key), f"{value:,.2f}"] for key, value in totals.items()]]))
        story.append(Spacer(1, 12))

        breakdown = payload.get("floor_breakdown", [])
        story.append(Paragraph("Group Breakdown", heading_style))
        breakdown_data = [["Group", "Rows", "Totals"]]
        for item in breakdown:
            totals_text = ", ".join(f"{key}={value:,.2f}" for key, value in item.get("totals", {}).items()) or "No totals"
            breakdown_data.append([str(item.get("group", "")), str(item.get("row_count", 0)), totals_text])
        story.append(self._pdf_table(breakdown_data))
        story.append(Spacer(1, 12))

        story.append(Paragraph("Recommended Actions", heading_style))
        for item in payload.get("recommended_actions", []):
            story.append(Paragraph(f"• {html.escape(str(item))}", styles["BodyText"]))

        document.build(story)
        return True

    @staticmethod
    def _pdf_table(rows: list[list[str]]):
        from reportlab.lib import colors
        from reportlab.platypus import Table, TableStyle

        table = Table(rows, repeatRows=1)
        table.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#17333d")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#d8ccb9")),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#fbf7ef")),
                    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#fbf7ef"), colors.HexColor("#f4ecdf")]),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("LEFTPADDING", (0, 0), (-1, -1), 8),
                    ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ]
            )
        )
        return table

    @staticmethod
    def _to_float(value: str) -> float | None:
        cleaned = str(value).strip().replace(",", "")
        if not cleaned:
            return None
        match = re.search(r"-?\d+(?:\.\d+)?", cleaned)
        if not match:
            return None
        try:
            return float(match.group(0))
        except ValueError:
            return None

    @staticmethod
    def _slugify(value: str) -> str:
        slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
        return slug or f"report-{uuid4().hex[:6]}"

    @staticmethod
    def _best_group_entry(breakdown: list[dict[str, Any]]) -> dict[str, Any] | None:
        ranked_entries = []
        for item in breakdown:
            totals = item.get("totals", {})
            if not totals:
                continue
            best_total = max(abs(float(value)) for value in totals.values())
            ranked_entries.append((best_total, item))
        if not ranked_entries:
            return None
        ranked_entries.sort(key=lambda entry: entry[0], reverse=True)
        return ranked_entries[0][1]
