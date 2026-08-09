from __future__ import annotations

import json
import zipfile
from datetime import UTC, datetime
from pathlib import Path

from .generators import (
    generate_docx,
    generate_markdown,
    generate_pdf,
    generate_text,
    sha256_file,
)
from .parser import detect_format, parse_document
from .storage import StudioStorage, safe_filename
from .templates import get_profile
from .verifier import verify_docx, verify_pdf

SUPPORTED_FORMATS = {"docx", "pdf", "markdown", "text"}


class ConversionService:
    def __init__(self, storage: StudioStorage):
        self.storage = storage

    def create(self, title: str, source: str, source_format: str = "auto") -> dict:
        actual_format = detect_format(source) if source_format == "auto" else source_format
        parse_document(source, title, actual_format)
        return self.storage.create_project(
            title.strip() or "Untitled document", source, actual_format
        )

    def correct(
        self, project_id: str, source: str, source_format: str = "auto", title: str | None = None
    ) -> dict:
        actual_format = detect_format(source) if source_format == "auto" else source_format
        parse_document(source, title or "Untitled document", actual_format)
        return self.storage.add_version(project_id, source, actual_format, title)

    def generate(
        self,
        project_id: str,
        formats: list[str],
        template_id: str = "standard_business_brief",
        version: int | None = None,
    ) -> dict:
        project = self.storage.get_project(project_id)
        version = version or int(project["current_version"])
        requested = list(dict.fromkeys(format_name.lower() for format_name in formats))
        invalid = set(requested) - SUPPORTED_FORMATS
        if invalid or not requested:
            raise ValueError(
                f"Unsupported or empty formats: {', '.join(sorted(invalid)) or 'none'}"
            )
        profile = get_profile(template_id)
        source = self.storage.source(project_id, version)
        version_meta = next(item for item in project["versions"] if int(item["version"]) == version)
        parsed = parse_document(source, project["title"], version_meta["source_format"])
        artifact_dir = self.storage.version_dir(project_id, version) / "artifacts"
        artifact_dir.mkdir(parents=True, exist_ok=True)
        base_name = safe_filename(project["title"])
        output: list[dict] = []
        for format_name in requested:
            suffix = {"docx": ".docx", "pdf": ".pdf", "markdown": ".md", "text": ".txt"}[
                format_name
            ]
            path = artifact_dir / f"{base_name}{suffix}"
            if format_name == "docx":
                artifact = generate_docx(parsed, profile, path)
                artifact.verification = verify_docx(path, artifact_dir)
            elif format_name == "pdf":
                artifact = generate_pdf(parsed, profile, path)
                artifact.verification = verify_pdf(path, artifact_dir)
            elif format_name == "markdown":
                artifact = generate_markdown(parsed, path)
            else:
                artifact = generate_text(parsed, path)
            data = artifact.as_dict()
            self.storage.record_artifact(project_id, version, data)
            output.append(data)
        return {
            "project_id": project_id,
            "version": version,
            "template": profile.as_dict(),
            "artifacts": output,
        }

    def export_package(self, project_id: str, version: int | None = None) -> Path:
        project = self.storage.get_project(project_id)
        version = version or int(project["current_version"])
        version_dir = self.storage.version_dir(project_id, version)
        export_dir = version_dir / "exports"
        export_dir.mkdir(parents=True, exist_ok=True)
        export_path = export_dir / f"{safe_filename(project['title'])}-v{version}.zip"
        files = [
            path
            for path in version_dir.rglob("*")
            if path.is_file() and export_dir not in path.parents
        ]
        manifest = {
            "schema": "ai-clean-paste-export/v1",
            "project_id": project_id,
            "title": project["title"],
            "version": version,
            "created_at": datetime.now(UTC).isoformat(timespec="seconds"),
            "files": [
                {
                    "path": str(path.relative_to(version_dir)),
                    "sha256": sha256_file(path),
                    "size": path.stat().st_size,
                }
                for path in files
            ],
        }
        with zipfile.ZipFile(export_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in files:
                archive.write(path, path.relative_to(version_dir))
            archive.writestr("manifest.json", json.dumps(manifest, indent=2, sort_keys=True))
        return export_path
