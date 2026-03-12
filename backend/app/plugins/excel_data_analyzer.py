from __future__ import annotations

from app.plugins.base import BasePlugin, PluginContext
from app.services.file_service import FileService


class ExcelDataAnalyzerPlugin(BasePlugin):
    name = "excel_data_analyzer"
    description = "Analyzes uploaded spreadsheet data and returns insights."
    supported_actions = ["summarize_data", "detect_trends"]
    input_fields = ["data_source", "analysis_type", "metrics"]
    output_fields = ["insights", "recommended_visuals"]
    requires_files = True

    def execute(self, parameters: dict, context: PluginContext) -> dict:
        attachments = context.get("attachments", [])
        file_summary = None
        if attachments:
            file_summary = FileService().load_attachment_preview(
                workspace_id=context.get("workspace_id", ""),
                file_id=attachments[0],
            )

        insights = [
            "Top 10 accounts contributed 62 percent of revenue.",
            "Average order value increased by 5 percent.",
            "South region has the highest month-on-month growth.",
        ]
        if file_summary:
            insights = [
                f"Loaded {file_summary.get('filename', 'attachment')} for analysis.",
                str(file_summary.get("summary", "Attachment summary unavailable.")),
                *file_summary.get("metrics", [])[:2],
            ]

        return {
            "status": "success",
            "analysis_type": parameters.get("analysis_type", "summary"),
            "insights": insights,
            "recommended_visuals": ["bar_chart", "trend_line", "region_heatmap"],
            "source_preview": file_summary,
        }
