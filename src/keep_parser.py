import json
import hashlib
import os
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Union


class KeepParseError(ValueError):
    """Raised when a Takeout source cannot be parsed safely."""


@dataclass
class KeepLabel:
    id: str
    name: str


@dataclass
class KeepChecklistItem:
    text: str
    checked: bool


@dataclass
class KeepAttachment:
    file_path: str
    mime_type: Optional[str] = None
    data: Optional[bytes] = None
    source_path: Optional[str] = None


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
    checklist: List[KeepChecklistItem]
    annotations: List[dict]
    attachments: List[KeepAttachment]
    raw: Dict[str, Any]
    source_path: Optional[str] = None
    source_hash: Optional[str] = None


@dataclass
class _SourcePayload:
    payload: dict
    source_path: str
    source_bytes: bytes
    media: Dict[str, tuple]


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
        for source in self._iter_note_payloads(path):
            note = self.parse_note(source.payload)
            note.source_path = source.source_path
            note.source_hash = hashlib.sha256(source.source_bytes).hexdigest()
            self._attach_media(note, source.media)
            notes.append(self._as_note_dict(note))
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
        for source in self._iter_note_payloads(path):
            note = self.parse_note(source.payload)
            note.source_path = source.source_path
            note.source_hash = hashlib.sha256(source.source_bytes).hexdigest()
            self._attach_media(note, source.media)
            parsed_notes.append(note)
        return parsed_notes

    def _iter_note_payloads(self, path: Path) -> Iterable[_SourcePayload]:
        # Takeout may arrive either as an extracted folder or as a single ZIP archive.
        if path.is_dir():
            media = {
                str(candidate.relative_to(path)): (candidate.read_bytes(), str(candidate))
                for candidate in path.rglob("*")
                if candidate.is_file() and candidate.suffix.lower() != ".json"
            }
            for file_path in self._find_json_files(path):
                raw_bytes = file_path.read_bytes()
                yield _SourcePayload(self._load_json_bytes(raw_bytes, str(file_path)), str(file_path), raw_bytes, media)
            return

        # ZIP-based import: we walk the archive contents instead of calling the Google API.
        if path.is_file() and path.suffix.lower() == ".zip":
            try:
                with zipfile.ZipFile(path, "r") as archive:
                    members = archive.namelist()
                    json_members = [name for name in members if self._is_keep_json(name)]
                    if not json_members:
                        json_members = [name for name in members if name.lower().endswith(".json")]
                    media = {name: (archive.read(name), name) for name in members if not name.endswith("/") and not name.lower().endswith(".json")}
                    for name in json_members:
                        raw_bytes = archive.read(name)
                        yield _SourcePayload(self._load_json_bytes(raw_bytes, f"{path}!{name}"), name, raw_bytes, media)
            except (zipfile.BadZipFile, EOFError, OSError) as error:
                raise KeepParseError(f"Unable to read Takeout ZIP {path}: {error}") from error
            return

        raise ValueError(f"Unsupported Takeout source: {path}")

    def _find_json_files(self, root: Path) -> List[Path]:
        # Filter to JSON files from Keep-related folders when possible, otherwise fall back
        # to all JSON files in the export tree. This keeps directory imports flexible.
        matches: List[Path] = []
        for candidate in root.rglob("*"):
            if not candidate.is_file() or candidate.suffix.lower() != ".json":
                continue
            rel = candidate.relative_to(root)
            if "Keep" in rel.parts or "keep" in rel.parts or "notes" in rel.parts:
                matches.append(candidate)
        if not matches:
            matches = list(root.rglob("*.json"))
        return sorted(matches)

    def _is_keep_json(self, name: str) -> bool:
        parts = [part.lower() for part in Path(name).parts]
        return name.lower().endswith(".json") and any(part in {"keep", "notes"} for part in parts)

    def _load_json_bytes(self, raw_bytes: bytes, source: str) -> dict:
        try:
            payload = json.loads(raw_bytes.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as error:
            raise KeepParseError(f"Malformed JSON in {source}: {error}") from error
        if not isinstance(payload, dict):
            raise KeepParseError(f"Keep note must be a JSON object in {source}")
        return payload

    def _load_json_file(self, path: Path) -> dict:
        # Local file ingestion: parse JSON from disk without any remote network access.
        return self._load_json_bytes(path.read_bytes(), str(path))

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
        labels = [KeepLabel(id=str(lbl.get("id", "")), name=str(lbl.get("name", ""))) for lbl in labels_raw if isinstance(lbl, dict)]
        checklist = [
            KeepChecklistItem(str(item.get("text", "")), bool(item.get("checked", False)))
            for item in raw.get("listContent", []) if isinstance(item, dict)
        ]

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
            checklist=checklist,
            annotations=list(raw.get("annotations", [])),
            attachments=[KeepAttachment(str(item.get("filePath", item.get("file_path", ""))), item.get("mimeType")) for item in raw.get("attachments", []) if isinstance(item, dict)],
            raw=dict(raw),
        )

    def _attach_media(self, note: KeepNote, media: Dict[str, tuple]) -> None:
        for attachment in note.attachments:
            for name, (data, source_path) in media.items():
                if name == attachment.file_path or Path(name).name == Path(attachment.file_path).name:
                    attachment.data = data
                    attachment.source_path = source_path
                    break

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
            "checklist": [{"text": item.text, "checked": item.checked} for item in note.checklist],
            "annotations": note.annotations,
            "attachments": [
                {"file_path": item.file_path, "mime_type": item.mime_type, "data": item.data, "source_path": item.source_path}
                for item in note.attachments
            ],
            "raw": note.raw,
            "source_path": note.source_path,
            "source_hash": note.source_hash,
        }
