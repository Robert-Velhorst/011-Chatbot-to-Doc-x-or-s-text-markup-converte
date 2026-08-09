# Technical audit

## Starting point

The supplied workspace was not a Git worktree. It contained a working Chrome MV3 extension, a Python Windows clipboard companion, six Vitest tests, three Python tests, fixtures, build scripts, and previously packaged ZIP files. The 124-page goal prompt was external to the repository and was inspected as source material; it is not copied into the product.

The existing clipboard implementation was retained because its architecture matches the safe source-side pipeline:

- synchronous browser `copy` handling on supported provider pages;
- semantic HTML plus plain-text clipboard payloads;
- optional, permission-gated generic site support;
- Windows `AddClipboardFormatListener` rather than polling;
- recognized CF_HTML `SourceURL` allowlist;
- CF_HTML, RTF, and Unicode written together;
- loop prevention and no copied-content logs.

The build did not contain a document-conversion product, web UI, versioned storage, DOCX/PDF generator, render verifier, API, CLI, deployment configuration, CI, or the required audit documentation. Those are implemented in this revision.

## Current architecture

| Boundary | Implementation | Evidence |
| --- | --- | --- |
| Browser copy | MV3 TypeScript content scripts | `src/extension`, `tests/*.test.ts` |
| Native clipboard | Python/pywin32 tray process | `src/windows`, `tests/test_windows.py` |
| Semantic parser | Markdown-it plus safe HTML parser | `src/studio/cleanpaste_studio/parser.py` |
| Document model | typed blocks and inline spans | `models.py` |
| Templates | four explicit portable profiles | `templates.py` |
| Generators | DOCX, PDF, Markdown, text | `generators.py` |
| Verification | isolated Word-to-PDF and Poppler render checks | `verifier.py`, `word_render_helper.py` |
| Persistence | SQLite metadata plus immutable source files | `storage.py` |
| API/security | FastAPI, loopback/token guard, rate limiting | `app.py`, `security.py` |
| CLI | serve, convert, doctor | `cli.py` |
| UI | React 19 + Vite, real API state | `studio-ui` |
| Packaging | extension/companion/Studio ZIPs, Windows executables, source package, Docker | `scripts`, PyInstaller specs, `Dockerfile`, `docker-compose.yml` |
| HAI/ngrok | bounded artifact API and authenticated HTTPS launcher | `integrations/hai`, `app.py`, `scripts/run-ngrok.ps1` |

## Data ownership and invariants

- A project has one owner: the local operating-system user who controls the configured data directory. Team/multi-tenant authorization is not claimed.
- A source version is immutable after creation. Corrections create the next integer version.
- Generated files belong to one project version.
- Stored artifact metadata contains SHA-256 and byte size.
- Export manifests cover every included file with SHA-256.
- Audit rows never contain source text, project titles, source URLs, filenames, or content hashes.
- Project IDs must be 32 lowercase hexadecimal characters; artifact names must be basenames.
- Production mode and non-loopback binds require a configured token.
- Output verification status is `verified`, `unverified`, or `failed`; generation alone never implies visual verification.

## Dependency and supply-chain review

Runtime dependencies are bounded in `pyproject.toml`; frontend dependencies are locked in `package-lock.json`. The CI uses `npm ci` and Python 3.12. Direct runtime libraries are FastAPI/Starlette/Pydantic/Uvicorn, markdown-it-py, python-docx/lxml, ReportLab, Pillow, and pypdf. The frontend uses React, Vite, and Lucide. The extension keeps packaged MV3 code only.

No package is loaded from a CDN at runtime. No runtime analytics or error-reporting SDK exists. The Docker runtime drops root, uses a read-only root filesystem in Compose, and persists only `/data`. An owner-approved repository license remains unresolved; no distribution license is claimed.

## Known technical debt

- DOCX visual verification is Windows/Word-specific. Non-Windows deployments report structural-only status.
- SQLite schema migration version 1 is recorded, but downgrade migration automation is not needed until a second schema exists.
- Conversion executes synchronously in FastAPI's bounded thread handling. This avoids a fake worker system but means very large documents can occupy one request; Word renders are serialized to prevent resource exhaustion.
- The project list is bounded to 100 records per API request but does not yet expose full-text search or cursor pagination.
- The UI is English-only; UTF-8 content and Dutch documents are supported, but localized chrome is deferred.
- Authenticated smoke tests in third-party editors require user-owned signed-in sessions and remain a manual acceptance gate.
