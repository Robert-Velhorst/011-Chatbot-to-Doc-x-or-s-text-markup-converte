# October 23, 2026 stable upgrade

## Exact dependency and runtime baseline

All 13 original JavaScript declarations were compared with official npm latest metadata and pinned exactly. Lucide React is 1.61.0, Vite 8.3.5 and Chrome types 0.3.6; the remaining direct versions were already current. Node targets 26.12.1 and npm 12.2.1.

Python direct and build requirements were compared with public PyPI metadata and pinned, including FastAPI 0.161.1, Uvicorn 0.54.0, Pydantic 2.14.1, ReportLab 5.1.0, Pillow 13.0.0, pypdf 6.21.2, pytest 9.1.1, Ruff 0.17.2, Hatchling 1.32.4 and PyInstaller 6.22.3. `uv.lock` records exact transitive versions and artifact hashes. The test client uses httpx2 2.16.0, following the current [Starlette TestClient contract](https://starlette.dev/testclient/), instead of its deprecated httpx fallback. Normal launch and packaging scripts use Python 3.15.1 and the frozen lock; they do not keep using the previous Python 3.12 launcher.

## Actual database engine

The latest public SQLite release is [3.54.1](https://www.sqlite.org/download.html). Python 3.15.1 on the development host reports SQLite 3.53.1, so updating Python alone does not meet the database requirement. Studio now uses [APSW 3.54.1.0](https://rogerbinns.github.io/apsw/) with the current SQLite engine on supported Windows/Linux wheels. It does not modify a shared Python runtime DLL or silently fall back to its older engine.

The on-disk schema remains version 1 and uses the same SQLite database format. Connections retain the 15-second busy timeout, foreign keys, WAL and NORMAL synchronization. Explicit transactions roll back failed operations. Tests cover opening an original schema created through CPython's independent driver, preserving source/version data, new writes, native SQLite backup and restoration, integrity checks, idempotency and cascade deletion. These tests use synthetic files only; they do not migrate operator data.

Health and doctor report the actual app engine. Windows packaging explicitly includes APSW, and its headless smoke checks the shipped Python and SQLite versions without opening a browser or creating a tray icon. The standard desktop launch remains available.

## Hetzner and operational acceptance

Hetzner remains the production target under `DEPLOYMENT_TARGET.md`. Keep Compose bound to loopback with a strong token and private persistent data volume. Before remote cutover, verify authenticated TLS, firewall/proxy boundaries, actual data counts, restore into a separate volume, and image/data rollback. Stop writes and preserve the entire SQLite database plus project-file tree as explained in `docs/OPERATOR_RUNBOOK.md`. Do not delete a real volume as part of an upgrade.

The runtime image uses pinned Python 3.15.1 / Node 26.12.1 build stages on Debian Trixie. Runtime packages receive distribution updates during build. Container checks must establish authenticated conversion into all four formats, artifact checksums and persistence after restart, with synthetic data and no external network. Distribution Poppler, platform Word-rendering acceptance and a complete image vulnerability scan remain separate evidence; this refresh does not assert that these external tools or every OS component match the highest upstream version.

Local JavaScript checks/tests/builds passed. Local Python installation failed for lack of disk space; no Python pass is inferred from that partial environment. Hosted Linux/Windows source tests, vulnerability audits, actual container execution and the packaged Windows smoke are required to establish readiness. No production deployment, operator data migration, real clipboard operation, provider call, signing or release publication is performed by this draft.
