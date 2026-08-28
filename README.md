# anykeep

A local-first, privacy-focused syncing utility designed to bridge Google Keep and Anytype via Google Takeout exports.

## Overview

`anykeep` provides a reliable, self-hosted pipeline to migrate and mirror your notes, checklists, and media attachments directly into your local Anytype vault without relying on brittle cloud APIs or complex OAuth setups.

## Key Features & Capabilities

* **Manual & Automated Ingestion**: Run one-off imports via command-line arguments or let a background directory watcher automatically process newly downloaded Takeout ZIP archives.
* **Zero-Cloud Security**: Eliminates OAuth apps, client secrets, and master tokens. Your Anytype Local API key is stored securely in your operating system's native credential vault using `keyring`.
* **Idempotent State Tracking**: Utilizes a local SQLite database (`state.db`) and SHA256 file hashing to track sync states and prevent duplicate note imports.
* **Comprehensive Extraction**: Gracefully parses nested note structures, including body text, checklist states, user labels, and embedded media attachments (images, audio, drawings).

## Project Structure

```text
anykeep/
├── config.yaml.example       # Sample configuration file
├── requirements.txt          # Python dependencies
├── state.db                  # Local SQLite database (auto-generated)
├── src/
│   ├── __init__.py
│   ├── cli.py                # Command-line interface entry point (Click)
│   ├── config.py             # YAML loader & OS Keyring integration
│   ├── db.py                 # SQLite database manager for tracking sync_map and hashes
│   ├── takeout_watcher.py    # Directory observer (watchdog) for ZIP automation
│   ├── keep_parser.py        # Parses raw Takeout JSON, HTML, and media refs
│   ├── transformer.py        # Converts Keep JSON objects into Anytype payloads
│   └── anytype_client.py     # Communicates with Anytype's Desktop Local REST API
├── tests/
│   ├── test_parser.py
│   └── test_transformer.py
└── README.md
```

# Default Configuration Setup
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

# CLI Commands to be Implemented
- anykeep auth --set-key: Securely saves your Anytype Local API key to the OS keyring.  
- anykeep pull --source <path>: Manually ingests an extracted Keep folder or Takeout ZIP archive.  
- anykeep watch: Monitors your download directory in the background for new Takeout archives.  
- anykeep status: Displays a summary table of synced notes, unpushed items, and media counts.  
