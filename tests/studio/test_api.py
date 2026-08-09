from pathlib import Path

from cleanpaste_studio.app import create_app
from cleanpaste_studio.config import Settings
from fastapi.testclient import TestClient


def client(tmp_path: Path, **overrides) -> TestClient:
    settings = Settings(data_dir=tmp_path / "data", **overrides)
    return TestClient(create_app(settings))


def test_critical_api_path(tmp_path: Path):
    with client(tmp_path) as web:
        assert web.get("/health").json()["status"] == "ok"
        created = web.post(
            "/api/projects",
            json={"title": "API brief", "source": "# Hello\n\n- one", "source_format": "auto"},
        )
        assert created.status_code == 201
        project = created.json()
        generated = web.post(
            f"/api/projects/{project['id']}/generate",
            json={"formats": ["markdown", "text"], "template_id": "standard_business_brief"},
        )
        assert generated.status_code == 200
        result = generated.json()
        assert {item["format"] for item in result["artifacts"]} == {"markdown", "text"}
        source = web.get(f"/api/projects/{project['id']}/source").json()
        assert source["source"] == "# Hello\n\n- one"
        download = web.get(
            f"/api/projects/{project['id']}/versions/1/artifacts/{result['artifacts'][0]['name']}"
        )
        assert download.status_code == 200
        package = web.post(f"/api/projects/{project['id']}/export")
        assert package.status_code == 200
        assert package.headers["content-type"] == "application/zip"


def test_token_auth_size_limit_and_security_headers(tmp_path: Path):
    with client(tmp_path, token="correct", max_source_bytes=10) as web:
        unauthorized = web.get("/api/projects")
        assert unauthorized.status_code == 401
        headers = {"Authorization": "Bearer correct"}
        assert web.get("/api/projects", headers=headers).status_code == 200
        too_large = web.post(
            "/api/projects",
            headers=headers,
            json={"title": "x", "source": "more than ten bytes", "source_format": "plain"},
        )
        assert too_large.status_code == 413
        assert web.get("/health").headers["x-content-type-options"] == "nosniff"

        session = web.post("/api/session", json={"token": "correct"})
        assert session.status_code == 200
        session_cookie = session.cookies.get("clean_paste_session")
        assert session_cookie
        assert session_cookie != "correct"

        logout = web.delete("/api/session")
        assert logout.status_code == 204
        assert web.get("/api/templates").status_code == 401
        assert web.get("/api/projects").status_code == 401


def test_production_and_non_loopback_require_token(tmp_path: Path):
    for settings in (
        Settings(data_dir=tmp_path / "prod", environment="production"),
        Settings(data_dir=tmp_path / "lan", host="0.0.0.0"),
    ):
        try:
            create_app(settings)
        except RuntimeError as exc:
            assert "token" in str(exc).lower()
        else:
            raise AssertionError("Unsafe server configuration unexpectedly accepted")


def test_privacy_contract_and_not_found_paths(tmp_path: Path):
    with client(tmp_path) as web:
        privacy = web.get("/api/privacy").json()
        assert privacy["telemetry"] is False
        assert privacy["cloud_processing"] is False
        assert privacy["copied_content_logging"] is False
        assert web.get("/api/projects/not-valid").status_code == 404
        assert web.get("/api/projects/not-valid/source").status_code == 404


def test_idempotency_key_prevents_duplicate_projects(tmp_path: Path):
    with client(tmp_path) as web:
        headers = {"Idempotency-Key": "create-fixture-0001"}
        payload = {"title": "Once", "source": "One source", "source_format": "plain"}
        first = web.post("/api/projects", headers=headers, json=payload)
        second = web.post("/api/projects", headers=headers, json=payload)
        assert first.status_code == second.status_code == 201
        assert first.json()["id"] == second.json()["id"]
        assert len(web.get("/api/projects").json()) == 1


def test_hai_connector_is_authenticated_bounded_and_idempotent(tmp_path: Path):
    with client(tmp_path, token="connector-secret") as web:
        headers = {
            "Authorization": "Bearer connector-secret",
            "Idempotency-Key": "hai-conversion-0001",
        }
        capabilities = web.get("/api/connectors/hai/v1/capabilities", headers=headers)
        assert capabilities.status_code == 200
        assert capabilities.json()["authority"] == "artifact_generation_only"
        assert capabilities.json()["external_mutation"] is False

        payload = {
            "title": "HAI brief",
            "source": "# HAI brief\n\n- bounded\n- local",
            "source_format": "markdown",
            "formats": ["markdown", "text"],
        }
        first = web.post("/api/connectors/hai/v1/convert", headers=headers, json=payload)
        second = web.post("/api/connectors/hai/v1/convert", headers=headers, json=payload)
        assert first.status_code == second.status_code == 201
        assert first.json() == second.json()
        assert first.json()["schema"] == "ai-clean-paste-hai/v1"
        assert all(
            item["download_url"].startswith("/api/projects/") for item in first.json()["artifacts"]
        )
        invalid_key = web.post(
            "/api/connectors/hai/v1/convert",
            headers={"Authorization": "Bearer connector-secret", "Idempotency-Key": "bad"},
            json=payload,
        )
        assert invalid_key.status_code == 422
        assert web.get("/api/connectors/hai/v1/capabilities").status_code == 401
