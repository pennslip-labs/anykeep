import json
import os
import zipfile
from pathlib import Path
import pytest
from click.testing import CliRunner

from src.cli import main
from src.config import load_config, DEFAULT_CONFIG, get_config_path
from src.keep_parser import KeepParser

def test_cli_help():
    """Test that the main CLI entry point outputs help info correctly."""
    runner = CliRunner()
    result = runner.invoke(main, ['--help'])
    assert result.exit_code == 0
    assert "Anykeep: Seamlessly sync Google Keep Takeout exports to Anytype." in result.output
    assert "auth" in result.output
    assert "pull" in result.output
    assert "watch" in result.output
    assert "status" in result.output

def test_auth_no_flag():
    """Test running 'auth' without --set-key prompts the usage hint."""
    runner = CliRunner()
    result = runner.invoke(main, ['auth'])
    assert result.exit_code == 0
    assert "Use --set-key to store your API key." in result.output

def test_load_config_defaults(monkeypatch, tmp_path):
    """Test loading configuration falls back to DEFAULT_CONFIG when config file is missing."""
    # Point home or config path to a temp directory by mocking Path.home()
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    
    config = load_config()
    assert config == DEFAULT_CONFIG
    assert config["anytype"]["host"] == "127.0.0.1"
    assert config["anytype"]["port"] == 3100


def test_parser_reads_takeout_zip(tmp_path):
    """Takeout ZIPs should be parsed locally without making any Google OAuth calls."""
    keep_dir = tmp_path / "Takeout" / "Keep"
    keep_dir.mkdir(parents=True)

    payload = {
        "title": "Test note",
        "textContent": "hello from takeout",
        "labels": [{"name": "work"}],
        "color": "blue",
        "isTrashed": False,
        "isArchived": False,
    }
    note_path = keep_dir / "note_1.json"
    note_path.write_text(json.dumps(payload), encoding="utf-8")

    zip_path = tmp_path / "takeout.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.write(note_path, arcname="Takeout/Keep/note_1.json")

    parser = KeepParser()
    notes = parser.list_notes(zip_path)

    assert len(notes) == 1
    assert notes[0]["title"] == "Test note"
    assert notes[0]["body"] == "hello from takeout"
