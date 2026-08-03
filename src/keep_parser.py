from dataclasses import dataclass
from typing import List, Optional

try:
    import google.auth
    from googleapiclient.discovery import build
except ImportError:  # pragma: no cover - exercised when optional deps are missing
    google = None
    build = None


@dataclass
class KeepLabel:
    id: str
    name: str


@dataclass
class KeepNote:
    id: str
    title: str
    body: str
    created_at: str
    updated_at: str
    pinned: bool
    archived: bool
    trashed: bool
    color: Optional[str]
    labels: List[KeepLabel]


class KeepParser:
    def __init__(self, service=None, credentials=None, scopes=None):
        self.service = service
        self.credentials = credentials
        self.scopes = scopes or ["https://www.googleapis.com/auth/keep.readonly"]

    def _build_service(self):
        if self.service is not None:
            return self.service

        if build is None or google is None:
            raise ImportError(
                "google-auth and google-api-python-client are required for live Google Keep access"
            )

        if self.credentials is None:
            creds, _ = google.auth.default(scopes=self.scopes)
            self.credentials = creds

        self.service = build("keep", "v1", credentials=self.credentials)
        return self.service

    def list_notes(self):
        """Fetch all notes metadata."""
        response = self._build_service().notes().list().execute()
        return response.get("notes", [])

    def get_note(self, note_id: str):
        """Fetch full note content."""
        return self._build_service().notes().get(name=f"notes/{note_id}").execute()

    def parse_note(self, raw: dict) -> KeepNote:
        """Convert raw Keep API JSON into our internal dataclass."""
        title = raw.get("title", "")
        body = raw.get("textContent", "")
        created_at = raw.get("createTime")
        updated_at = raw.get("updateTime")

        pinned = raw.get("pinned", False)
        archived = raw.get("archived", False)
        trashed = raw.get("trashed", False)

        color = raw.get("color")

        labels_raw = raw.get("labels", [])
        labels = [
            KeepLabel(id=lbl.get("id"), name=lbl.get("name"))
            for lbl in labels_raw
        ]

        note_name = raw.get("name") or ""
        note_id = note_name.split("/")[-1] if note_name else ""

        return KeepNote(
            id=note_id,
            title=title,
            body=body,
            created_at=created_at,
            updated_at=updated_at,
            pinned=pinned,
            archived=archived,
            trashed=trashed,
            color=color,
            labels=labels
        )

    def fetch_all_parsed_notes(self) -> List[KeepNote]:
        """High-level helper: list → fetch → parse."""
        notes_meta = self.list_notes()
        parsed_notes = []

        for meta in notes_meta:
            note_id = meta["name"].split("/")[-1]
            raw_note = self.get_note(note_id)
            parsed_notes.append(self.parse_note(raw_note))

        return parsed_notes
