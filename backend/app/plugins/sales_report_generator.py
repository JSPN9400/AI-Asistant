from __future__ import annotations

from app.plugins.base import BasePlugin, PluginContext
from app.services.report_service import ReportService


class SalesReportGeneratorPlugin(BasePlugin):
    name = "sales_report_generator"
    description = "Generates weekly or monthly sales reports."
    supported_actions = ["generate_report", "summarize_sales"]
    input_fields = ["data_source", "format", "period", "audience", "group_by"]
    output_fields = ["report", "highlights", "recommended_actions", "report_files", "floor_breakdown"]
    requires_files = True

    def __init__(self) -> None:
        self.report_service = ReportService()

    def execute(self, parameters: dict, context: PluginContext) -> dict:
        attachments = context.get("attachments", [])
        report_payload = self.report_service.build_report(
            workspace_id=str(context.get("workspace_id", "")),
            attachments=attachments,
            parameters=parameters,
            user_input=str(context.get("original_user_input", "")),
        )
        report_payload["attached_files"] = len(attachments)
        report_payload["format"] = parameters.get("format", "professional_report")
        report_payload["period"] = parameters.get("period", "weekly")
        report_payload["audience"] = parameters.get("audience", "sales_manager")
        return report_payload
