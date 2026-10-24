import shutil
import sqlite3
from pathlib import Path

import apsw
import pytest
from cleanpaste_studio.storage import StudioStorage


def test_actual_engine_and_connection_guards(tmp_path: Path):
    storage = StudioStorage(tmp_path / "data")
    assert tuple(map(int, apsw.sqlite_lib_version().split("."))) >= (3, 54, 1)
    with storage.connect() as db:
        assert db.execute("select sqlite_version() as version").fetchone()["version"] == "3.54.1"
        assert db.execute("pragma foreign_keys").fetchone()["foreign_keys"] == 1
        assert db.execute("pragma journal_mode").fetchone()["journal_mode"] == "wal"
        assert db.execute("pragma synchronous").fetchone()["synchronous"] == 1
        assert db.execute("pragma busy_timeout").fetchone()["timeout"] == 15000
        assert db.execute("pragma integrity_check").fetchone()["integrity_check"] == "ok"


def test_transaction_failure_rolls_back_all_statements(tmp_path: Path):
    storage = StudioStorage(tmp_path / "data")
    with pytest.raises(apsw.ConstraintError), storage.connect() as db:
        db.execute("insert into audit_events(event_type,created_at) values('rollback','now')")
        db.execute(
            "insert into versions(project_id,version,source_format,source_hash,created_at) "
            "values('missing-parent',1,'plain','synthetic','now')"
        )
    assert "rollback" not in storage.audit_summary()


def test_legacy_database_upgrade_and_native_backup_restore(tmp_path: Path):
    original = tmp_path / "legacy"
    original.mkdir()
    project_id = "a" * 32
    source = original / "projects" / project_id / "v0001"
    source.mkdir(parents=True)
    (source / "source.txt").write_text("Synthetic legacy document", encoding="utf-8")
    # Produce the original schema through CPython's independent SQLite driver.
    with sqlite3.connect(original / "studio.sqlite3") as legacy:
        legacy.executescript(
            "CREATE TABLE projects (id TEXT PRIMARY KEY,title TEXT NOT NULL,"
            "created_at TEXT NOT NULL,updated_at TEXT NOT NULL,"
            "current_version INTEGER NOT NULL DEFAULT 0);"
            "CREATE TABLE versions (project_id TEXT NOT NULL,version INTEGER NOT NULL,"
            "source_format TEXT NOT NULL,source_hash TEXT NOT NULL,created_at TEXT NOT NULL,"
            "PRIMARY KEY(project_id,version),"
            "FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE);"
        )
        legacy.execute(
            "INSERT INTO projects VALUES(?,?,?,?,?)",
            (project_id, "Synthetic legacy project", "then", "then", 1),
        )
        legacy.execute(
            "INSERT INTO versions VALUES(?,?,?,?,?)",
            (project_id, 1, "plain", "synthetic", "then"),
        )
    legacy.close()
    storage = StudioStorage(original)
    assert storage.get_project(project_id)["current_version"] == 1
    assert storage.source(project_id, 1) == "Synthetic legacy document"
    assert storage.add_version(project_id, "Synthetic new revision", "plain")["current_version"] == 2
    storage.idempotency_store("synthetic-retry-key", "upgrade", {"preserved": True})

    restored_dir = tmp_path / "restored"
    restored_dir.mkdir()
    source_db = apsw.Connection(str(storage.db_path))
    destination = apsw.Connection(str(restored_dir / "studio.sqlite3"))
    try:
        with destination.backup("main", source_db, "main") as backup:
            assert backup.step() is True
    finally:
        destination.close()
        source_db.close()
    shutil.copytree(storage.projects_dir, restored_dir / "projects")
    restored = StudioStorage(restored_dir)
    assert restored.get_project(project_id)["current_version"] == 2
    assert restored.source(project_id, 1) == "Synthetic legacy document"
    assert restored.source(project_id, 2) == "Synthetic new revision"
    assert restored.idempotency_get("synthetic-retry-key", "upgrade") == {"preserved": True}
    with restored.connect() as db:
        assert db.execute("pragma integrity_check").fetchone()["integrity_check"] == "ok"
        assert db.execute("pragma foreign_key_check").fetchall() == []
    restored.delete_project(project_id)
    with restored.connect() as db:
        assert db.execute("select count(*) as total from versions").fetchone()["total"] == 0


def test_old_runtime_fails_before_opening_database(tmp_path: Path, monkeypatch):
    monkeypatch.setattr(apsw, "sqlite_lib_version", lambda: "3.53.1")
    with pytest.raises(RuntimeError, match="SQLite 3.54.1"):
        StudioStorage(tmp_path / "data")
    assert not (tmp_path / "data" / "studio.sqlite3").exists()
