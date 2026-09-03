import hashlib
import json
import zipfile

import pytest

from src.keep_parser import KeepParseError, KeepParser


def test_parser_preserves_metadata_and_associates_zip_media(tmp_path):
	payload = {
		"name": "notes/note-1",
		"title": "Rich note",
		"textContent": "body",
		"listContent": [{"text": "ship it", "checked": True}],
		"annotations": [{"description": "link", "start": 0, "length": 4, "url": "https://example.test"}],
		"attachments": [{"filePath": "media/photo.jpg", "mimeType": "image/jpeg"}],
		"futureField": {"kept": True},
	}
	source = json.dumps(payload, separators=(",", ":")).encode("utf-8")
	archive_path = tmp_path / "export.zip"
	with zipfile.ZipFile(archive_path, "w") as archive:
		archive.writestr("takeout/KEEP/note.json", source)
		archive.writestr("takeout/media/photo.jpg", b"image bytes")

	note = KeepParser().fetch_all_parsed_notes(archive_path)[0]

	assert note.checklist[0].text == "ship it"
	assert note.checklist[0].checked is True
	assert note.annotations[0]["url"] == "https://example.test"
	assert note.raw["futureField"] == {"kept": True}
	assert note.attachments[0].data == b"image bytes"
	assert note.source_hash == hashlib.sha256(source).hexdigest()


def test_parser_reports_malformed_json_source(tmp_path):
	note_path = tmp_path / "Keep" / "bad.json"
	note_path.parent.mkdir()
	note_path.write_text("{bad", encoding="utf-8")

	with pytest.raises(KeepParseError, match="bad.json"):
		KeepParser().list_notes(tmp_path)


def test_parser_associates_media_in_extracted_directory(tmp_path):
	keep_dir = tmp_path / "Takeout" / "Keep"
	keep_dir.mkdir(parents=True)
	(keep_dir / "note.json").write_text(json.dumps({
		"title": "Directory note",
		"attachments": [{"filePath": "photo.png", "mimeType": "image/png"}],
	}), encoding="utf-8")
	(keep_dir / "photo.png").write_bytes(b"png bytes")

	note = KeepParser().fetch_all_parsed_notes(tmp_path)[0]

	assert note.attachments[0].data == b"png bytes"
