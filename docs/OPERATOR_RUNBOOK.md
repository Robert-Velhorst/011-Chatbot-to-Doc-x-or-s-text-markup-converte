# Operator runbook

## Start

```powershell
.\scripts\run-local.ps1
```

Health: `GET http://127.0.0.1:8765/health`
Readiness: `GET http://127.0.0.1:8765/readiness`

## Stop

Press `Ctrl+C` in the server terminal. The extension and tray companion each have their own visible enable/disable control; stopping one does not silently stop the others.

## Production-mode local service

Set `CLEAN_PASTE_ENV=production`, a strong `CLEAN_PASTE_TOKEN`, and keep the host at `127.0.0.1` unless a reviewed reverse proxy and TLS boundary exist. The built-in server is not claimed safe for direct internet exposure.

For the dependency-contained Windows build, double-click the Studio executable and use its tray menu to stop cleanly. For ngrok, follow `docs/NGROK.md`; never pool the converter with an unrelated endpoint. For HAI, use only the artifact-generation contract under `integrations/hai` and store the bearer token in HAI's approved local secret mechanism.

## Backup

Stop the server, then copy the entire configured `CLEAN_PASTE_DATA_DIR` to owner-controlled encrypted storage. Preserve `studio.sqlite3` and `projects` together. Verify the backup contains both and record its SHA-256 externally.

## Restore

Stop the server. Preserve the current data directory first. Restore the database and projects tree as one unit, start the server, check `/readiness`, list projects, open the latest version, and generate a disposable text artifact. Do not merge arbitrary database and project-tree snapshots.

## Incident response

- **Possible token leak:** stop, rotate token, restart, clear browser cookie.
- **ngrok endpoint conflict:** preserve the other tunnel; do not use pooling. Free capacity intentionally or use an account with another endpoint.
- **Repeated failed verification:** preserve source, generated artifact, and verification reason; do not label the artifact verified.
- **Database error:** stop writes, backup the whole data directory, run SQLite integrity checks on a copy.
- **Clipboard loop:** disable the tray companion; confirm only the expected process owns clipboard writes.
- **Unexpected network activity:** stop all surfaces. The product has no intended content network path; investigate process identity and dependencies.

## Rollback

Application rollback is source/package replacement plus restoration of the matching data backup. Schema version 1 is forward-compatible with this release. No destructive migration is run automatically.

## Logs

Uvicorn access logging is disabled by the CLI. Verification errors are returned to the initiating client. Audit event counts are available at `/api/privacy`; rows contain no document content.
