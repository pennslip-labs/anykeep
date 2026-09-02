import sqlite3

from src.db import DatabaseManager


def test_database_manager_creates_configured_database(tmp_path):
    db_path = tmp_path / "nested" / "state.db"

    database = DatabaseManager(db_path)
    try:
        assert database.db_path == db_path
        assert db_path.exists()
        assert isinstance(database.connection, sqlite3.Connection)
        columns = database.connection.execute("PRAGMA table_info(sync_map)").fetchall()
        assert [column["name"] for column in columns] == [
            "keep_file_id",
            "file_hash",
            "anytype_object_id",
            "sync_status",
            "media_count",
            "last_synced_at",
            "error_message",
        ]

        database.connection.execute("CREATE TABLE test (value TEXT)")
        database.connection.execute("INSERT INTO test VALUES (?)", ("ready",))
        database.connection.commit()
        row = database.connection.execute("SELECT value FROM test").fetchone()
        assert row["value"] == "ready"
    finally:
        database.close()


def test_database_manager_closes_connection(tmp_path):
    with DatabaseManager(tmp_path / "state.db") as database:
        assert database.connection.execute("SELECT 1").fetchone()[0] == 1

    try:
        database.connection.execute("SELECT 1")
    except sqlite3.ProgrammingError:
        pass
    else:
        raise AssertionError("database connection should be closed")


def test_database_manager_schema_is_idempotent(tmp_path):
    db_path = tmp_path / "state.db"

    first_database = DatabaseManager(db_path)
    first_database.close()
    second_database = DatabaseManager(db_path)

    try:
        table_count = second_database.connection.execute(
            "SELECT COUNT(*) AS count FROM sqlite_master "
            "WHERE type = 'table' AND name = 'sync_map'"
        ).fetchone()["count"]
        assert table_count == 1
    finally:
        second_database.close()


def test_sync_record_helpers_insert_update_and_query(tmp_path):
    with DatabaseManager(tmp_path / "state.db") as database:
        database.insert_sync_record("note-1", "hash-1", "PENDING")

        assert database.get_sync_status("note-1") == "PENDING"
        assert database.get_sync_status("missing") is None

        updated = database.update_sync_record(
            "note-1",
            file_hash="hash-2",
            anytype_object_id="object-1",
            sync_status="PUSHED",
            media_count=2,
        )

        assert updated is True
        record = database.get_sync_record("note-1")
        assert record["file_hash"] == "hash-2"
        assert record["anytype_object_id"] == "object-1"
        assert record["sync_status"] == "PUSHED"
        assert record["media_count"] == 2
        assert database.update_sync_record("missing", sync_status="ERROR") is False


def test_sync_record_helpers_support_upsert_and_clearing_nullable_values(tmp_path):
    with DatabaseManager(tmp_path / "state.db") as database:
        database.upsert_sync_record("note-1", "hash-1", "PARSED", "object-1", 1)
        database.upsert_sync_record("note-1", "hash-2", "ERROR", error_message="failed")

        assert database.get_sync_record("note-1")["file_hash"] == "hash-2"
        assert database.get_sync_status("note-1") == "ERROR"
        assert database.update_sync_record("note-1", anytype_object_id=None) is True
        assert database.get_sync_record("note-1")["anytype_object_id"] is None