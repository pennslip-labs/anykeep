import os
import sys

import pytest

# Add the src directory to Python path
CURRENT_DIR = os.path.dirname(__file__)
SRC_PATH = os.path.abspath(os.path.join(CURRENT_DIR, "..", "src"))
sys.path.insert(0, SRC_PATH)

from keep_parser import KeepParser


def test_parse_note():
    mock_raw = {
        "name": "notes/12345",
        "title": "Test Note",
        "textContent": "This is a test body.",
        "createTime": "2024-01-01T12:00:00Z",
        "updateTime": "2024-01-02T12:00:00Z",
        "pinned": True,
        "archived": False,
        "trashed": False,
        "color": "RED",
        "labels": [
            {"id": "lbl1", "name": "Work"},
            {"id": "lbl2", "name": "Ideas"},
        ],
    }

    parser = KeepParser()
    parsed = parser.parse_note(mock_raw)

    assert parsed.id == "12345"
    assert parsed.title == "Test Note"
    assert parsed.body == "This is a test body."
    assert parsed.pinned is True
    assert parsed.color == "RED"
    assert [label.name for label in parsed.labels] == ["Work", "Ideas"]


@pytest.mark.integration
def test_live_google_keep_connection_optional():
    """Exercise the live Google Keep API path when credentials exist."""
    parser = KeepParser()

    try:
        notes = parser.list_notes()
    except ImportError as exc:
        pytest.skip(f"Google client dependencies are not installed: {exc}")
    except Exception as exc:  # pragma: no cover - depends on environment
        pytest.skip(f"Live Google Keep access unavailable: {exc}")

    assert isinstance(notes, list)
