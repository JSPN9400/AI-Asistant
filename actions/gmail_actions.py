import base64
from email.mime.text import MIMEText

_gmail = None


def _client():
    global _gmail
    if _gmail is None:
        try:
            from integrations.google.gmail_client import GmailClient
        except Exception as exc:
            raise RuntimeError(
                "Gmail integration is unavailable right now. "
                "Check the Google client dependencies and credentials."
            ) from exc
        _gmail = GmailClient()
    return _gmail


def read_emails(limit: int = 5) -> str:
    msgs = _client().list_messages(max_results=limit)
    subjects: list[str] = []
    for msg in msgs:
        headers = msg.get("payload", {}).get("headers", [])
        subject = next(
            (h["value"] for h in headers if h.get("name") == "Subject"),
            "(no subject)",
        )
        subjects.append(subject)
    if not subjects:
        return "No recent emails found."
    return "Your latest emails: " + " | ".join(subjects)


def send_email(to: str, subject: str, body: str) -> str:
    if not to:
        return "I need a recipient email address."

    client = _client()
    service = client.service
    message = MIMEText(body or "")
    message["to"] = to
    message["subject"] = subject or ""
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()
    service.users().messages().send(userId="me", body={"raw": raw}).execute()
    return f"Sent email to {to}."

