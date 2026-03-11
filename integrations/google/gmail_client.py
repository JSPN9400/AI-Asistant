from googleapiclient.discovery import build

from .auth import get_credentials


class GmailClient:
    def __init__(self) -> None:
        self.creds = get_credentials()
        self.service = build("gmail", "v1", credentials=self.creds)

    def list_messages(self, max_results: int = 5) -> list[dict]:
        results = (
            self.service.users()
            .messages()
            .list(userId="me", maxResults=max_results)
            .execute()
        )
        messages = results.get("messages", [])
        details: list[dict] = []
        for msg in messages:
            full = (
                self.service.users()
                .messages()
                .get(userId="me", id=msg["id"])
                .execute()
            )
            details.append(full)
        return details

