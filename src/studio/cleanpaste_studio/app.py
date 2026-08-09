from __future__ import annotations

import mimetypes
import os
import sys
from pathlib import Path
from typing import Literal
from urllib.parse import quote

from fastapi import FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from . import __version__
from .config import Settings
from .security import SecurityMiddleware, SessionStore
from .service import ConversionService
from .storage import StudioStorage
from .templates import PROFILES


class ProjectInput(BaseModel):
    title: str = Field(min_length=1, max_length=180)
    source: str = Field(min_length=1)
    source_format: Literal["auto", "markdown", "html", "plain"] = "auto"


class CorrectionInput(ProjectInput):
    pass


class GenerationInput(BaseModel):
    formats: list[Literal["docx", "pdf", "markdown", "text"]] = Field(min_length=1, max_length=4)
    template_id: str = "standard_business_brief"
    version: int | None = Field(default=None, ge=1)

    @field_validator("formats")
    @classmethod
    def unique_formats(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))


class SessionInput(BaseModel):
    token: str = Field(min_length=1, max_length=512)


class HAIConversionInput(ProjectInput):
    formats: list[Literal["docx", "pdf", "markdown", "text"]] = Field(
        default_factory=lambda: ["markdown", "text"], min_length=1, max_length=4
    )
    template_id: str = "standard_business_brief"

    @field_validator("formats")
    @classmethod
    def unique_hai_formats(cls, values: list[str]) -> list[str]:
        return list(dict.fromkeys(values))


def _ui_dist() -> Path:
    configured = os.environ.get("CLEAN_PASTE_UI_DIR")
    if configured:
        return Path(configured).resolve()
    bundle_root = getattr(sys, "_MEIPASS", None)
    if bundle_root:
        return Path(bundle_root) / "studio-ui" / "dist"
    source_layout = Path(__file__).resolve().parents[3] / "studio-ui" / "dist"
    if source_layout.is_dir():
        return source_layout
    return Path.cwd() / "studio-ui" / "dist"


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    settings.validate()
    storage = StudioStorage(settings.data_dir)
    service = ConversionService(storage)
    sessions = SessionStore()
    app = FastAPI(
        title="AI Clean Paste Document Studio",
        version=__version__,
        docs_url="/api/docs" if not settings.production else None,
        redoc_url=None,
        openapi_url="/api/openapi.json" if not settings.production else None,
    )
    app.state.settings = settings
    app.state.storage = storage
    app.state.service = service
    app.add_middleware(SecurityMiddleware, settings=settings, sessions=sessions)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "version": __version__}

    @app.get("/readiness")
    def readiness() -> dict:
        return {
            "status": "ready",
            "storage": str(settings.data_dir),
            "environment": settings.environment,
            "authentication": "token" if settings.token else "loopback-only development",
        }

    @app.get("/api/templates")
    def templates() -> list[dict]:
        return [profile.as_dict() for profile in PROFILES.values()]

    @app.post("/api/session")
    def create_session(payload: SessionInput, response: Response) -> dict:
        import secrets

        if not settings.token or not secrets.compare_digest(payload.token, settings.token):
            raise HTTPException(401, "Invalid local access token")
        response.set_cookie(
            "clean_paste_session",
            sessions.issue(),
            httponly=True,
            samesite="strict",
            secure=False,
            max_age=8 * 60 * 60,
            path="/api",
        )
        return {"status": "unlocked"}

    @app.delete("/api/session", status_code=204)
    def delete_session(request: Request, response: Response):
        sessions.revoke(request.cookies.get("clean_paste_session"))
        response.delete_cookie("clean_paste_session", path="/api")

    @app.get("/api/projects")
    def projects(limit: int = Query(50, ge=1, le=100)) -> list[dict]:
        return storage.list_projects(limit)

    @app.post("/api/projects", status_code=201)
    def create_project(payload: ProjectInput, request: Request) -> dict:
        if len(payload.source.encode("utf-8")) > settings.max_source_bytes:
            raise HTTPException(413, "Source document exceeds the configured size limit")
        try:
            key = request.headers.get("Idempotency-Key")
            cached = storage.idempotency_get(key, "create_project")
            if cached:
                return cached
            result = service.create(payload.title, payload.source, payload.source_format)
            storage.idempotency_store(key, "create_project", result)
            return result
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/projects/{project_id}")
    def get_project(project_id: str) -> dict:
        try:
            return storage.get_project(project_id)
        except (KeyError, ValueError) as exc:
            raise HTTPException(404, "Project not found") from exc

    @app.get("/api/projects/{project_id}/source")
    def get_source(project_id: str, version: int | None = Query(default=None, ge=1)) -> dict:
        try:
            project = storage.get_project(project_id)
            actual_version = version or int(project["current_version"])
            meta = next(
                item for item in project["versions"] if int(item["version"]) == actual_version
            )
            return {
                "project_id": project_id,
                "version": actual_version,
                "title": project["title"],
                "source_format": meta["source_format"],
                "source": storage.source(project_id, actual_version),
            }
        except (KeyError, ValueError, StopIteration) as exc:
            raise HTTPException(404, "Project version not found") from exc

    @app.post("/api/projects/{project_id}/versions", status_code=201)
    def add_version(project_id: str, payload: CorrectionInput) -> dict:
        if len(payload.source.encode("utf-8")) > settings.max_source_bytes:
            raise HTTPException(413, "Source document exceeds the configured size limit")
        try:
            return service.correct(project_id, payload.source, payload.source_format, payload.title)
        except KeyError as exc:
            raise HTTPException(404, "Project not found") from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.post("/api/projects/{project_id}/generate")
    def generate(project_id: str, payload: GenerationInput, request: Request) -> dict:
        try:
            key = request.headers.get("Idempotency-Key")
            operation = f"generate:{project_id}"
            cached = storage.idempotency_get(key, operation)
            if cached:
                return cached
            result = service.generate(
                project_id, payload.formats, payload.template_id, payload.version
            )
            storage.idempotency_store(key, operation, result)
            return result
        except KeyError as exc:
            raise HTTPException(404, "Project or version not found") from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    @app.get("/api/projects/{project_id}/versions/{version}/artifacts/{name}")
    def download_artifact(project_id: str, version: int, name: str):
        try:
            path = storage.artifact_path(project_id, version, name)
        except (KeyError, ValueError) as exc:
            raise HTTPException(404, "Artifact not found") from exc
        media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        return FileResponse(path, media_type=media_type, filename=path.name)

    @app.post("/api/projects/{project_id}/export")
    def export_project(project_id: str, version: int | None = Query(default=None, ge=1)):
        try:
            path = service.export_package(project_id, version)
        except (KeyError, ValueError) as exc:
            raise HTTPException(404, "Project or version not found") from exc
        return FileResponse(path, media_type="application/zip", filename=path.name)

    @app.delete("/api/projects/{project_id}", status_code=204)
    def delete_project(project_id: str):
        try:
            storage.delete_project(project_id)
        except (KeyError, ValueError) as exc:
            raise HTTPException(404, "Project not found") from exc

    @app.get("/api/privacy")
    def privacy() -> dict:
        return {
            "telemetry": False,
            "cloud_processing": False,
            "clipboard_history": False,
            "copied_content_logging": False,
            "audit_event_counts": storage.audit_summary(),
        }

    @app.get("/api/connectors/hai/v1/capabilities")
    def hai_capabilities() -> dict:
        return {
            "connector": "ai-clean-paste",
            "version": __version__,
            "mode": "local-first",
            "authority": "artifact_generation_only",
            "input_formats": ["auto", "markdown", "html", "plain"],
            "output_formats": ["docx", "pdf", "markdown", "text"],
            "templates": list(PROFILES),
            "max_source_bytes": settings.max_source_bytes,
            "telemetry": False,
            "external_mutation": False,
        }

    @app.post("/api/connectors/hai/v1/convert", status_code=201)
    def hai_convert(payload: HAIConversionInput, request: Request) -> dict:
        if len(payload.source.encode("utf-8")) > settings.max_source_bytes:
            raise HTTPException(413, "Source document exceeds the configured size limit")
        try:
            key = request.headers.get("Idempotency-Key")
            cached = storage.idempotency_get(key, "hai_convert")
            if cached:
                return cached
            project = service.create(payload.title, payload.source, payload.source_format)
            generated = service.generate(
                project["id"], payload.formats, payload.template_id, version=1
            )
            base = f"/api/projects/{project['id']}/versions/1/artifacts"
            artifacts = [
                {**artifact, "download_url": f"{base}/{quote(artifact['name'])}"}
                for artifact in generated["artifacts"]
            ]
            result = {
                "schema": "ai-clean-paste-hai/v1",
                "authority": "artifact_generation_only",
                "project_id": project["id"],
                "version": 1,
                "artifacts": artifacts,
                "export_url": f"/api/projects/{project['id']}/export?version=1",
            }
            storage.idempotency_store(key, "hai_convert", result)
            return result
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc

    ui_dist = _ui_dist()
    assets = ui_dist / "assets"
    if assets.is_dir():
        app.mount("/assets", StaticFiles(directory=assets), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def ui(path: str):
        index = ui_dist / "index.html"
        if index.is_file():
            return FileResponse(index)
        return HTMLResponse(
            "<h1>AI Clean Paste Document Studio</h1><p>UI is not built. Run <code>npm run studio:build</code>.</p>",
            status_code=503,
        )

    return app


app = create_app()
