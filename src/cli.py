# cli.py
"""
The top level command line orchastrator. using click to expose 
four primary commands as listed by the MVP documentation
"""
import os
import sys
from pathlib import Path
import keyring
import click
import hashlib
import json

from .config import load_config, set_api_key
from .db import DatabaseManager
from .keep_parser import KeepParser
from .takeout_watcher import start_watcher

KEYRING_SERVICE_NAME = "anykeep"
KEYRING_USERNAME = "anytype_local_api_key"

@click.group()
@click.option('--config', default=None, help='Path to custom config YAML file.')
@click.pass_context
def main(ctx, config):
    """Anykeep: Seamlessly sync Google Keep Takeout exports to Anytype."""
    # Ensure context object is initialized as a dictionary for sharing state across commands
    ctx.ensure_object(dict)
    try:
        # Step: Load YAML configuration (and fallback to defaults if missing)
        ctx.obj['CONFIG'] = load_config()
    except Exception as e:
        click.echo(f"ERROR: {e}", err=True)
        sys.exit(1)

@main.command()
@click.option('--set-key', is_flag=True, help='Prompt and store Anytype Local API key in OS keyring.')
def auth(set_key):
    """Authenticate and store your Anytype Local API key securely."""
    if set_key:
        try:
            api_key = click.prompt(
                "Enter your Anytype Local API key",
                hide_input=True,
            )
            set_api_key(api_key)
            click.echo("SUCCESS: Anytype API key securely saved to OS keyring.")
        except Exception as e:
            click.echo(f"ERROR: Failed to save API key to keyring: {e}", err=True)
            sys.exit(1)
    else:
        click.echo("Use --set-key to store your API key.")

@main.command()
@click.option('--source', required=True, type=click.Path(exists=True), help='Path to Takeout ZIP archive or Keep folder.')
@click.pass_context
def pull(ctx, source):
    """Manually ingest and sync a Google Takeout export."""
    click.echo(f"Starting manual import from: {source}")
    # 1. Extract ZIP if necessary (or read directory)
    # 2. Initialize DB manager & Anytype client
    # 3. Loop through notes, hash JSON, check sqlite state.db for deduplication
    # 4. Transform notes & media attachments, push to Anytype Local API
    
	# TODO: implement pull

@main.command()
@click.pass_context
def watch(ctx):
    """Start background directory watcher for automatic Takeout syncing."""
    config = ctx.obj['CONFIG']
    ingestion_config = config.get('ingestion', {})
    watch_directory = Path(ingestion_config.get('watch_directory', '~/Downloads')).expanduser()
    auto_delete_zip = bool(ingestion_config.get('auto_delete_zip', True))

    click.echo(f"Watching for Takeout archives in: {watch_directory}")
    try:
        start_watcher(
            watch_directory,
            lambda archive: _process_takeout_archive(archive, config),
            auto_delete_zip=auto_delete_zip,
        )
    except OSError as error:
        raise click.ClickException(str(error)) from error


def _process_takeout_archive(archive: Path, config: dict) -> None:
    """Parse a watched archive and persist its current state for later sync."""
    parser = KeepParser()
    notes = parser.list_notes(archive)
    db_path = config.get('storage', {}).get('db_path')

    with DatabaseManager(db_path) as database:
        for note in notes:
            note_id = str(note.get('id') or note.get('title') or archive.name)
            file_hash = hashlib.sha256(
                json.dumps(note, sort_keys=True, separators=(',', ':')).encode('utf-8')
            ).hexdigest()
            existing = database.get_sync_record(note_id)
            if existing and existing['file_hash'] == file_hash:
                continue
            database.upsert_sync_record(note_id, file_hash, 'PARSED')

@main.command()
@click.pass_context
def status(ctx):
    """Display sync status dashboard and audit logs."""
    click.echo("--- Anykeep Sync Status ---")
    # 1. Query state.db for summary statistics:
    #    - Total synced notes
    #    - Media attachments uploaded
    #    - Pending/Error items count
    # 2. Format output cleanly using click / tabulate or custom printing
    
	# TODO: implement status

if __name__ == "__main__":
    main()

	