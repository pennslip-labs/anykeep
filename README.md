# anykeep

A local-first, privacy-focused syncing utility for importing Google Keep notes from Google Takeout exports into Anytype.

## Overview

`anykeep` is intentionally offline-first. It reads exported Keep data from Google Takeout ZIP files or extracted Keep folders on disk and converts those notes into Anytype-ready structures.

This project does not use live Google API calls, OAuth, or browser-based account authorization. All input is expected to come from an exported ZIP or extracted Takeout folder already downloaded to the machine.

## What this project expects

Incoming data should be a Google Takeout export containing Keep data. The parser works from local files only.

## Supported input

- A Google Takeout ZIP file
- An extracted Takeout directory containing Keep JSON files
- A `Takeout/Keep/`-style folder layout

## Key Features & Capabilities

* **Local-only ingestion**: Reads exported Keep files from disk instead of contacting Google services.
* **Privacy-first workflow**: No OAuth client secrets, refresh tokens, or Google auth flows.
* **Manual and automated ingest**: Accepts either a ZIP path or a local extracted folder, and can later be extended to watch a download directory.
* **Idempotent state tracking**: Keeps a local database and hash-based checks to avoid duplicate imports.
* **Note parsing**: Extracts note text, labels, metadata, and archive/trash state from Takeout JSON.

## Example usage

Pass a sample Takeout ZIP directly:

```bash
python - <<'PY'
from src.keep_parser import KeepParser

parser = KeepParser()
notes = parser.list_notes('tests/sample/takeout-20260901T183337Z-1-001.zip')
print(notes[:3])
PY
```

You can also point the parser at an extracted Keep directory instead of a ZIP:

```bash
python - <<'PY'
from src.keep_parser import KeepParser

parser = KeepParser()
notes = parser.list_notes('/path/to/Takeout')
print(notes[:3])
PY
```

You can also set a path through the environment variable `GOOGLE_TAKEOUT_PATH`:

```bash
export GOOGLE_TAKEOUT_PATH="/path/to/Takeout"
python - <<'PY'
from src.keep_parser import KeepParser

parser = KeepParser()
notes = parser.list_notes()
print(notes[:3])
PY
```

## Project structure

```text
anykeep/
├── requirements.txt
├── README.md
├── src/
│   ├── __init__.py
│   ├── cli.py
│   ├── config.py
│   ├── db.py
│   ├── keep_parser.py
│   ├── takeout_watcher.py
│   ├── transformer.py
│   └── anytype_client.py
├── tests/
│   ├── sample/
│   └── test_cli_config.py
├── state.db
└── .venv/
```

## Default configuration setup

```yaml
anytype:
  host: "127.0.0.1"
  port: 3100
  target_space_id: "SPACE_ID"

ingestion:
  watch_directory: "~/Downloads"
  auto_delete_zip: true

storage:
  db_path: "~/.config/anykeep/state.db"
  log_level: "INFO"
```

## CLI commands to be implemented

- `anykeep auth --set-key`: securely saves your Anytype Local API key to the OS keyring.
- `anykeep pull --source <path>`: manually ingests an extracted Keep folder or Takeout ZIP archive.
- `anykeep watch`: monitors a download directory for new Takeout archives.
- `anykeep status`: displays a summary of synced notes and media counts.

## Current import contract

The parser intentionally treats Google Takeout as a local file input format. The import path is:

- download Takeout ZIP locally
- point the parser at that ZIP or extracted folder
- read Keep JSON files from disk
- convert them into note dictionaries or dataclass objects for downstream sync work

There is no Google API client or OAuth lifecycle in this project at this stage.

