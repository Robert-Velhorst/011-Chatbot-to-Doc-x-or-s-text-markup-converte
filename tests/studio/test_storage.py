import json
import zipfile
from pathlib import Path

import pytest
from cleanpaste_studio.service import ConversionService
from cleanpaste_studio.storage import StudioStorage


def test_versioning_export_and_deletion(tmp_path: Path):
    storage = StudioStorage(tmp_path / "data")
    service = ConversionService(storage)
    project = service.create("Private brief", "# First", "markdown")
    corrected = service.correct(project["id"], "# Second", "markdown", "Private brief")
    assert corrected["current_version"] == 2
    assert storage.source(project["id"], 1) == "# First"
    assert storage.source(project["id"], 2) == "# Second"

    service.generate(project["id"], ["markdown", "text"])
    export_path = service.export_package(project["id"])
    with zipfile.ZipFile(export_path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
        assert manifest["schema"] == "ai-clean-paste-export/v1"
        assert "source.txt" in archive.namelist()
        assert all(item["sha256"] for item in manifest["files"])

    project_dir = storage.project_dir(project["id"])
    storage.delete_project(project["id"])
    assert not project_dir.exists()
    with pytest.raises(KeyError):
        storage.get_project(project["id"])


def test_path_traversal_is_rejected(tmp_path: Path):
    storage = StudioStorage(tmp_path)
    with pytest.raises(ValueError):
        storage.project_dir("../../outside")
    project = storage.create_project("x", "source", "plain")
    with pytest.raises(ValueError):
        storage.artifact_path(project["id"], 1, "../source.txt")


def test_audit_log_never_persists_content_title_url_or_hash(tmp_path: Path):
    storage = StudioStorage(tmp_path)
    secret = "NEVER-PERSIST-IN-AUDIT"
    storage.create_project(secret, f"https://private.example/{secret}", "plain")
    raw_db = storage.db_path.read_bytes()
    # Source/title exist in their intended stores, so inspect only the audit rows for the privacy boundary.
    with storage.connect() as db:
        events = [dict(row) for row in db.execute("SELECT * FROM audit_events")]
    serialized = json.dumps(events)
    assert secret not in serialized
    assert "private.example" not in serialized
    assert set(events[0]) == {"id", "event_type", "project_id", "version", "created_at"}
    assert raw_db
