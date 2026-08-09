from __future__ import annotations

import hashlib
import json
import re
import shutil
import sqlite3
import threading
import uuid
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path


def _utcnow() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def safe_filename(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._ -]+", "", value).strip(" .")
    value = re.sub(r"\s+", "-", value)
    return value[:80] or "document"


class StudioStorage:
    """SQLite metadata plus immutable source files under a private local data directory."""

    def __init__(self, data_dir: Path):
        self.data_dir = data_dir.resolve()
        self.projects_dir = self.data_dir / "projects"
        self.db_path = self.data_dir / "studio.sqlite3"
        self._lock = threading.RLock()
        self.projects_dir.mkdir(parents=True, exist_ok=True)
        self._initialize()

    @contextmanager
    def connect(self):
        connection = sqlite3.connect(self.db_path, timeout=15)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA synchronous = NORMAL")
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self.connect() as db:
            db.execute("PRAGMA journal_mode = WAL")
            db.execute("PRAGMA synchronous = NORMAL")
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    current_version INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS versions (
                    project_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    source_format TEXT NOT NULL,
                    source_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(project_id, version),
                    FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS artifacts (
                    project_id TEXT NOT NULL,
                    version INTEGER NOT NULL,
                    format TEXT NOT NULL,
                    name TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    size INTEGER NOT NULL,
                    verification_json TEXT,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(project_id, version, format),
                    FOREIGN KEY(project_id, version) REFERENCES versions(project_id, version) ON DELETE CASCADE
                );
                CREATE TABLE IF NOT EXISTS audit_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    project_id TEXT,
                    version INTEGER,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS idempotency_keys (
                    key TEXT NOT NULL,
                    operation TEXT NOT NULL,
                    response_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    PRIMARY KEY(key, operation)
                );
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_projects_updated_at
                    ON projects(updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_artifacts_project_version
                    ON artifacts(project_id, version DESC);
                """
            )
            db.execute(
                "INSERT OR IGNORE INTO schema_migrations(version,applied_at) VALUES(1,?)",
                (_utcnow(),),
            )

    def project_dir(self, project_id: str) -> Path:
        if not re.fullmatch(r"[0-9a-f]{32}", project_id):
            raise ValueError("Invalid project identifier")
        target = (self.projects_dir / project_id).resolve()
        if self.projects_dir not in target.parents:
            raise ValueError("Project path escapes storage root")
        return target

    def version_dir(self, project_id: str, version: int) -> Path:
        if version < 1:
            raise ValueError("Version must be positive")
        return self.project_dir(project_id) / f"v{version:04d}"

    def create_project(self, title: str, source: str, source_format: str) -> dict:
        project_id = uuid.uuid4().hex
        created_at = _utcnow()
        source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
        target = self.version_dir(project_id, 1)
        target.mkdir(parents=True)
        (target / "source.txt").write_text(source, encoding="utf-8")
        with self._lock, self.connect() as db:
            db.execute(
                "INSERT INTO projects(id,title,created_at,updated_at,current_version) VALUES(?,?,?,?,1)",
                (project_id, title, created_at, created_at),
            )
            db.execute(
                "INSERT INTO versions(project_id,version,source_format,source_hash,created_at) VALUES(?,?,?,?,?)",
                (project_id, 1, source_format, source_hash, created_at),
            )
            self._audit(db, "project_created", project_id, 1)
        return self.get_project(project_id)

    def add_version(
        self, project_id: str, source: str, source_format: str, title: str | None = None
    ) -> dict:
        with self._lock, self.connect() as db:
            row = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            if not row:
                raise KeyError(project_id)
            version = int(row["current_version"]) + 1
            created_at = _utcnow()
            source_hash = hashlib.sha256(source.encode("utf-8")).hexdigest()
            target = self.version_dir(project_id, version)
            target.mkdir(parents=True)
            (target / "source.txt").write_text(source, encoding="utf-8")
            db.execute(
                "INSERT INTO versions(project_id,version,source_format,source_hash,created_at) VALUES(?,?,?,?,?)",
                (project_id, version, source_format, source_hash, created_at),
            )
            db.execute(
                "UPDATE projects SET title=COALESCE(?,title),updated_at=?,current_version=? WHERE id=?",
                (title, created_at, version, project_id),
            )
            self._audit(db, "version_created", project_id, version)
        return self.get_project(project_id)

    def get_project(self, project_id: str) -> dict:
        with self.connect() as db:
            row = db.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
            if not row:
                raise KeyError(project_id)
            versions = [
                dict(item)
                for item in db.execute(
                    "SELECT version,source_format,source_hash,created_at FROM versions WHERE project_id=? ORDER BY version DESC",
                    (project_id,),
                )
            ]
            artifacts = [
                self._artifact_row(item)
                for item in db.execute(
                    "SELECT * FROM artifacts WHERE project_id=? ORDER BY version DESC,format",
                    (project_id,),
                )
            ]
        data = dict(row)
        data["versions"] = versions
        data["artifacts"] = artifacts
        return data

    def list_projects(self, limit: int = 50) -> list[dict]:
        limit = max(1, min(limit, 100))
        with self.connect() as db:
            return [
                dict(row)
                for row in db.execute(
                    "SELECT id,title,created_at,updated_at,current_version FROM projects ORDER BY updated_at DESC LIMIT ?",
                    (limit,),
                )
            ]

    def source(self, project_id: str, version: int) -> str:
        path = self.version_dir(project_id, version) / "source.txt"
        if not path.is_file():
            raise KeyError((project_id, version))
        return path.read_text(encoding="utf-8")

    def record_artifact(self, project_id: str, version: int, artifact: dict) -> None:
        with self._lock, self.connect() as db:
            db.execute(
                """INSERT OR REPLACE INTO artifacts
                (project_id,version,format,name,sha256,size,verification_json,created_at)
                VALUES(?,?,?,?,?,?,?,?)""",
                (
                    project_id,
                    version,
                    artifact["format"],
                    artifact["name"],
                    artifact["sha256"],
                    artifact["size"],
                    json.dumps(artifact.get("verification"), separators=(",", ":")),
                    _utcnow(),
                ),
            )
            self._audit(db, "artifact_generated", project_id, version)

    def artifact_path(self, project_id: str, version: int, name: str) -> Path:
        if Path(name).name != name:
            raise ValueError("Invalid artifact name")
        target = (self.version_dir(project_id, version) / "artifacts" / name).resolve()
        root = self.version_dir(project_id, version).resolve()
        if root not in target.parents or not target.is_file():
            raise KeyError(name)
        return target

    def delete_project(self, project_id: str) -> None:
        target = self.project_dir(project_id)
        with self._lock, self.connect() as db:
            exists = db.execute("SELECT 1 FROM projects WHERE id=?", (project_id,)).fetchone()
            if not exists:
                raise KeyError(project_id)
            db.execute("DELETE FROM projects WHERE id=?", (project_id,))
            self._audit(db, "project_deleted", project_id, None)
        if target.exists():
            shutil.rmtree(target)

    def audit_summary(self) -> dict:
        with self.connect() as db:
            rows = db.execute(
                "SELECT event_type,COUNT(*) count FROM audit_events GROUP BY event_type ORDER BY event_type"
            ).fetchall()
        return {row["event_type"]: row["count"] for row in rows}

    def idempotency_get(self, key: str | None, operation: str) -> dict | None:
        if not key:
            return None
        if not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", key):
            raise ValueError("Invalid Idempotency-Key")
        with self.connect() as db:
            row = db.execute(
                "SELECT response_json FROM idempotency_keys WHERE key=? AND operation=?",
                (key, operation),
            ).fetchone()
        return json.loads(row["response_json"]) if row else None

    def idempotency_store(self, key: str | None, operation: str, response: dict) -> None:
        if not key:
            return
        if not re.fullmatch(r"[A-Za-z0-9._:-]{8,128}", key):
            raise ValueError("Invalid Idempotency-Key")
        with self._lock, self.connect() as db:
            db.execute(
                "INSERT OR IGNORE INTO idempotency_keys(key,operation,response_json,created_at) VALUES(?,?,?,?)",
                (key, operation, json.dumps(response, separators=(",", ":")), _utcnow()),
            )

    @staticmethod
    def _audit(
        db: sqlite3.Connection, event_type: str, project_id: str | None, version: int | None
    ) -> None:
        # Privacy boundary: event metadata only. Never source content, title, URL, filename, or hash.
        db.execute(
            "INSERT INTO audit_events(event_type,project_id,version,created_at) VALUES(?,?,?,?)",
            (event_type, project_id, version, _utcnow()),
        )

    @staticmethod
    def _artifact_row(row: sqlite3.Row) -> dict:
        result = dict(row)
        result["verification"] = json.loads(result.pop("verification_json") or "null")
        return result
