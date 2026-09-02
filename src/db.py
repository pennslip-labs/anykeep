"""SQLite connection management for Anykeep's local state database."""

import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional, Union


DEFAULT_DB_PATH = "~/.config/anykeep/state.db"
DatabasePath = Union[str, Path]
_UNSET = object()
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sync_map (
	keep_file_id TEXT PRIMARY KEY,
	file_hash TEXT NOT NULL,
	anytype_object_id TEXT,
	sync_status TEXT NOT NULL,
	media_count INTEGER DEFAULT 0,
	last_synced_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
	error_message TEXT
);
"""


class DatabaseManager:
	"""Open and manage the connection to Anykeep's local SQLite database."""

	def __init__(self, db_path: Optional[DatabasePath] = None):
		self.db_path = Path(db_path or DEFAULT_DB_PATH).expanduser()
		self.db_path.parent.mkdir(parents=True, exist_ok=True)
		self.connection = sqlite3.connect(self.db_path)
		self.connection.row_factory = sqlite3.Row
		self.initialize_schema()

	def initialize_schema(self) -> None:
		"""Create the local state tables if they do not already exist."""
		self.connection.executescript(SCHEMA_SQL)
		self.connection.commit()

	def insert_sync_record(
		self,
		keep_file_id: str,
		file_hash: str,
		sync_status: str,
		anytype_object_id: Optional[str] = None,
		media_count: int = 0,
		error_message: Optional[str] = None,
	) -> None:
		"""Insert a new note tracking record."""
		self.connection.execute(
			"""
			INSERT INTO sync_map (
				keep_file_id, file_hash, anytype_object_id, sync_status,
				media_count, error_message
			) VALUES (?, ?, ?, ?, ?, ?)
			""",
			(keep_file_id, file_hash, anytype_object_id, sync_status, media_count, error_message),
		)
		self.connection.commit()

	def update_sync_record(
		self,
		keep_file_id: str,
		*,
		file_hash: Any = _UNSET,
		anytype_object_id: Any = _UNSET,
		sync_status: Any = _UNSET,
		media_count: Any = _UNSET,
		error_message: Any = _UNSET,
	) -> bool:
		"""Update supplied fields for a note and refresh its sync timestamp."""
		updates: Dict[str, Any] = {
			"file_hash": file_hash,
			"anytype_object_id": anytype_object_id,
			"sync_status": sync_status,
			"media_count": media_count,
			"error_message": error_message,
		}
		updates = {column: value for column, value in updates.items() if value is not _UNSET}
		if not updates:
			raise ValueError("At least one sync record field must be provided")

		set_clause = ", ".join(f"{column} = ?" for column in updates)
		parameters = [*updates.values(), keep_file_id]
		cursor = self.connection.execute(
			f"UPDATE sync_map SET {set_clause}, last_synced_at = CURRENT_TIMESTAMP "
			"WHERE keep_file_id = ?",
			parameters,
		)
		self.connection.commit()
		return cursor.rowcount == 1

	def upsert_sync_record(
		self,
		keep_file_id: str,
		file_hash: str,
		sync_status: str,
		anytype_object_id: Optional[str] = None,
		media_count: int = 0,
		error_message: Optional[str] = None,
	) -> None:
		"""Insert a record or replace its tracked values when it already exists."""
		self.connection.execute(
			"""
			INSERT INTO sync_map (
				keep_file_id, file_hash, anytype_object_id, sync_status,
				media_count, error_message
			) VALUES (?, ?, ?, ?, ?, ?)
			ON CONFLICT(keep_file_id) DO UPDATE SET
				file_hash = excluded.file_hash,
				anytype_object_id = excluded.anytype_object_id,
				sync_status = excluded.sync_status,
				media_count = excluded.media_count,
				last_synced_at = CURRENT_TIMESTAMP,
				error_message = excluded.error_message
			""",
			(keep_file_id, file_hash, anytype_object_id, sync_status, media_count, error_message),
		)
		self.connection.commit()

	def get_sync_record(self, keep_file_id: str) -> Optional[sqlite3.Row]:
		"""Return one note tracking record, or None when it is not known."""
		return self.connection.execute(
			"SELECT * FROM sync_map WHERE keep_file_id = ?",
			(keep_file_id,),
		).fetchone()

	def get_sync_status(self, keep_file_id: str) -> Optional[str]:
		"""Return the current sync status for one note, or None when it is unknown."""
		record = self.get_sync_record(keep_file_id)
		return record["sync_status"] if record is not None else None

	def close(self) -> None:
		"""Close the database connection."""
		self.connection.close()

	def __enter__(self) -> "DatabaseManager":
		return self

	def __exit__(self, exc_type, exc_value, traceback) -> None:
		self.close()
