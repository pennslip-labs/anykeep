import json
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional, Union


@dataclass
class KeepLabel:
    id: str
    name: str


@dataclass
class KeepNote:
    id: str
    title: str
    body: str
    created_at: Optional[str]
    updated_at: Optional[str]
    pinned: bool
    archived: bool
    trashed: bool
    color: Optional[str]
    labels: List[KeepLabel]


class KeepParser:
    """Parse note data from a Google Takeout export.

    This implementation is intentionally local-only: it reads exported Keep JSON
    files from disk and never calls the Google API. That distinction is important
    because the repo is designed around Takeout import, not live OAuth access.
    """

    def __init__(self, source: Optional[Union[str, os.PathLike]] = None):
        # Storage for the default Takeout source used when callers do not pass a path.
        self.source = Path(source) if source is not None else None

    def list_notes(self, source: Optional[Union[str, os.PathLike]] = None) -> List[dict]:
        """Return a list of note dicts from a Takeout ZIP or extracted Keep folder."""
        # Accept either an explicit path or an environment-provided Takeout location.
        path = Path(source) if source is not None else self.source
        if path is None:
            env_path = os.getenv("GOOGLE_TAKEOUT_PATH")
            if env_path:
                path = Path(env_path)

        if path is None:
            raise FileNotFoundError(
                "No Takeout source provided. Pass a zip path, directory, or set GOOGLE_TAKEOUT_PATH."
            )

        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Takeout path does not exist: {path}")

        notes: List[dict] = []
        for raw in self._iter_note_payloads(path):
            notes.append(self._as_note_dict(self.parse_note(raw)))
        return notes

    def fetch_all_parsed_notes(self, source: Optional[Union[str, os.PathLike]] = None) -> List[KeepNote]:
        """Return fully parsed note objects from the Takeout source."""
        path = Path(source) if source is not None else self.source
        if path is None:
            env_path = os.getenv("GOOGLE_TAKEOUT_PATH")
            if env_path:
                path = Path(env_path)

        if path is None:
            raise FileNotFoundError(
                "No Takeout source provided. Pass a zip path, directory, or set GOOGLE_TAKEOUT_PATH."
            )

        parsed_notes: List[KeepNote] = []
        for raw in self._iter_note_payloads(path):
            parsed_notes.append(self.parse_note(raw))
        return parsed_notes

    def _iter_note_payloads(self, path: Path) -> Iterable[dict]:
        # Takeout may arrive either as an extracted folder or as a single ZIP archive.
        if path.is_dir():
            for file_path in self._find_json_files(path):
                yield self._load_json_file(file_path)
            return

        # ZIP-based import: we walk the archive contents instead of calling the Google API.
        if path.is_file() and path.suffix.lower() == ".zip":
            with zipfile.ZipFile(path, "r") as archive:
                for name in archive.namelist():
                    if name.endswith(".json") and ("/Keep/" in name or name.endswith("Keep.json") or "/Keep" in name):
                        with archive.open(name) as handle:
                            yield json.loads(handle.read().decode("utf-8"))
            return

        raise ValueError(f"Unsupported Takeout source: {path}")

    def _find_json_files(self, root: Path) -> List[Path]:
        # Filter to JSON files from Keep-related folders when possible, otherwise fall back
        # to all JSON files in the export tree. This keeps directory imports flexible.
        matches: List[Path] = []
        for candidate in root.rglob("*.json"):
            rel = candidate.relative_to(root)
            if "Keep" in rel.parts or "keep" in rel.parts or "notes" in rel.parts:
                matches.append(candidate)
        if not matches:
            matches = list(root.rglob("*.json"))
        return sorted(matches)

    def _load_json_file(self, path: Path) -> dict:
        # Local file ingestion: parse JSON from disk without any remote network access.
        with open(path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def parse_note(self, raw: dict) -> KeepNote:
        """Convert a raw Keep JSON object into a note dataclass."""
        # Normalize the Takeout payload into the project's internal dataclass model.
        title = raw.get("title", "")
        body = raw.get("textContent") or raw.get("text") or ""
        created_at = raw.get("createTime")
        updated_at = raw.get("updateTime")
        pinned = bool(raw.get("pinned", False))
        archived = bool(raw.get("archived", False) or raw.get("isArchived", False))
        trashed = bool(raw.get("trashed", False) or raw.get("isTrashed", False))
        color = raw.get("color")

        labels_raw = raw.get("labels", [])
        labels = [KeepLabel(id=str(lbl.get("id", "")), name=lbl.get("name", "")) for lbl in labels_raw]

        note_name = raw.get("name") or ""
        note_id = note_name.split("/")[-1] if note_name else raw.get("id", "")

        return KeepNote(
            id=str(note_id),
            title=title,
            body=body,
            created_at=created_at,
            updated_at=updated_at,
            pinned=pinned,
            archived=archived,
            trashed=trashed,
            color=color,
            labels=labels,
        )

    def _as_note_dict(self, note: KeepNote) -> dict:
        # Keep the returned payload simple for downstream sync logic and tests.
        return {
            "id": note.id,
            "title": note.title,
            "body": note.body,
            "created_at": note.created_at,
            "updated_at": note.updated_at,
            "pinned": note.pinned,
            "archived": note.archived,
            "trashed": note.trashed,
            "color": note.color,
            "labels": [
                {"id": label.id, "name": label.name}
                for label in note.labels
            ],
        }
