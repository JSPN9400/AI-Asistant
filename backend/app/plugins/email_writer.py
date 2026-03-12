from __future__ import annotations

from app.plugins.base import BasePlugin, PluginContext


class EmailWriterPlugin(BasePlugin):
    name = "email_writer"
    description = "Drafts workplace emails and client responses."
    supported_actions = ["draft_email", "client_response"]
    input_fields = ["prompt", "tone", "recipient", "language"]
    output_fields = ["subject", "body"]

    def execute(self, parameters: dict, context: PluginContext) -> dict:
        tone = parameters.get("tone", "professional")
        prompt = parameters.get("prompt", "Draft a workplace email.")
        subject = "Follow-up on requested action"
        body = (
            f"Hello,\n\n"
            f"This is a {tone} draft based on the request:\n{prompt}\n\n"
            f"Regards,\n{context.get('user_id', 'Assistant User')}"
        )
        return {"status": "success", "subject": subject, "body": body}
