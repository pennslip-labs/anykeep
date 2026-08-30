import os
from pathlib import Path
import pytest
from click.testing import CliRunner

from src.cli import main
from src.config import load_config, DEFAULT_CONFIG, get_config_path

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
