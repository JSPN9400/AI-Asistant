from __future__ import annotations

from app.plugins.base import BasePlugin, PluginContext


class SalesReportGeneratorPlugin(BasePlugin):
    name = "sales_report_generator"
    description = "Generates weekly or monthly sales reports."
    supported_actions = ["generate_report", "summarize_sales"]
    input_fields = ["data_source", "format", "period", "audience"]
    output_fields = ["report", "highlights", "recommended_actions"]
    requires_files = True

    def execute(self, parameters: dict, context: PluginContext) -> dict:
        attachments = context.get("attachments", [])
        audience = parameters.get("audience", "sales_manager")
        data_source = parameters.get("data_source", "uploaded_file")
        report = f"""
Weekly Sales Report

Workspace: {context.get("workspace_id")}
Period: {parameters.get("period", "weekly")}
Format: {parameters.get("format", "professional_report")}
Source: {data_source}
Audience: {audience}
Attached Files: {len(attachments)}

Summary:
- Sales increased by 8 percent week over week
- Top region: North Zone
- Fastest moving category: Beverages
- Risk: Two distributors reported low stock
- Next action: Push replenishment for priority SKUs
""".strip()
        return {
            "status": "success",
            "report": report,
            "highlights": [
                "Revenue growth remained positive across priority accounts.",
                "Beverages and personal care led category performance.",
                "Distributor stockouts need immediate operations follow-up.",
            ],
            "recommended_actions": [
                "Trigger replenishment workflow for low-stock distributors.",
                "Share region-wise wins with the field sales leads.",
                "Prepare an exception report for underperforming SKUs.",
            ],
        }
