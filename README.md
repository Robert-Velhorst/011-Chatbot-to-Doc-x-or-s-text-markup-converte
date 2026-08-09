# AI Clean Paste

AI Clean Paste is a private, local-first toolkit for preserving the structure of AI-generated text.

It now has three connected surfaces:

1. **Chrome extension** — cleans the synchronous copy event on ChatGPT, Claude, Gemini, Copilot, Perplexity, Grok, and Manus. Rich browser editors receive semantic HTML; plain fields receive faithful text.
2. **Windows companion** — listens to clipboard-change notifications and upgrades recognized AI-origin CF_HTML with RTF for Word and Outlook. It has no keyboard hook or polling loop.
3. **Document Studio** — converts Markdown, sanitized HTML, or plain text into DOCX, PDF, Markdown, and text, preserves immutable source versions, verifies rendered output, and exports source plus checksums.

No surface sends document or clipboard content to a cloud service. There is no telemetry, clipboard history, copied-content logging, global key interception, or bundled AI provider key.

The release also includes dependency-contained Windows 11 folders for the Document Studio and clipboard companion, a production-mode ngrok launcher, and a bounded HAI connector contract.

## Fastest Windows 11 start

Unzip `AI-Clean-Paste-Studio-Windows-v0.2.0.zip`, then double-click `AI-Clean-Paste-Studio.exe`. The browser opens automatically. Use the **AI Clean Paste — Document Studio** tray icon to reopen or stop it. No Python, Node.js, Docker, or administrator access is required.

## Quick start: Document Studio

Windows PowerShell:

```powershell
.\scripts\run-local.ps1
```

Then open <http://127.0.0.1:8765>. The first run creates `.venv`, installs the locked project ranges, builds the React UI, and stores runtime data under `runtime/studio` unless `CLEAN_PASTE_DATA_DIR` is set.

Manual setup:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
npm.cmd install
npm.cmd run studio:build
$env:CLEAN_PASTE_DATA_DIR = "runtime/studio"
.\.venv\Scripts\clean-paste-studio.exe serve
```

Convert without the web UI:

```powershell
.\.venv\Scripts\clean-paste-studio.exe convert fixtures\studio\sample-brief.md `
  --out outputs\sample `
  --formats docx,pdf,markdown,text `
  --template standard_business_brief
```

Run diagnostics:

```powershell
.\.venv\Scripts\clean-paste-studio.exe doctor
```

## Chrome extension

```powershell
npm.cmd install
npm.cmd run check
npm.cmd test
npm.cmd run build
```

Open `chrome://extensions`, enable Developer mode, choose **Load unpacked**, and select `dist/chrome-extension`.

Supported providers are explicit and independently switchable. Unknown sites are off by default and require an optional per-site permission. Browser destinations need no injected paste handler.

## Windows companion

See [src/windows/README.md](src/windows/README.md). Its automatic mode transforms only clipboard entries whose CF_HTML `SourceURL` matches a supported provider. It writes Unicode text, CF_HTML, and RTF together and suppresses self-generated clipboard loops.

## HAI connector and ngrok

The bounded HAI interface is documented in [integrations/hai/README.md](integrations/hai/README.md) with a checked-in OpenAPI contract. It can generate and return versioned artifacts but has no browser, messaging, Google, or workflow-execution authority.

For a temporary authenticated HTTPS endpoint, generate a token as shown below and run:

```powershell
.\scripts\run-ngrok.ps1
```

The script keeps Studio bound to `127.0.0.1`, requires production mode plus a strong token, and stops its exact child process when the tunnel ends. See [docs/NGROK.md](docs/NGROK.md).

## Verification

Run the complete local gate:

```powershell
.\scripts\verify.ps1
```

The gate runs TypeScript checks, extension tests/build, Studio build, Python lint/tests, and a CLI conversion. PDF verification uses Poppler. On Windows, DOCX verification opens the file invisibly in Microsoft Word, exports it to PDF, renders the first page, and rejects blank output. On systems without Word, DOCX is explicitly reported as **structurally verified, visually unverified**.

## Security boundary

- Default bind: `127.0.0.1:8765`.
- A token is mandatory in production mode or for a non-loopback bind.
- ngrok exposure is supported only through token-authenticated production mode; never expose development mode.
- API rate limit: 60 requests/minute/client by default.
- Source limit: 2 MB by default.
- Unsafe link schemes and provider UI/script markup are removed.
- Project IDs and artifact filenames are validated against path traversal.
- Audit events record action type, project ID, version, and time—never source, title, URL, filename, or content hash.
- Runtime files, uploads, databases, environments, and secrets are ignored by Git.

Set a production token locally; never commit it:

```powershell
$env:CLEAN_PASTE_ENV = "production"
$tokenBytes = New-Object byte[] 32
$randomGenerator = [Security.Cryptography.RandomNumberGenerator]::Create()
$randomGenerator.GetBytes($tokenBytes)
$randomGenerator.Dispose()
$env:CLEAN_PASTE_TOKEN = [BitConverter]::ToString($tokenBytes).Replace("-", "")
```

## Documentation

- [Technical audit](docs/TECHNICAL_AUDIT.md)
- [Critical path](docs/CRITICAL_PATH.md)
- [Acceptance tests](docs/ACCEPTANCE_TESTS.md)
- [Completion matrix](docs/GOAL_COMPLETION_MATRIX.md)
- [Final verification](docs/FINAL_VERIFICATION_REPORT.md)
- [Security and threat model](docs/SECURITY.md)
- [Operator runbook](docs/OPERATOR_RUNBOOK.md)
- [UI action audit](docs/UI_ACTION_AUDIT.md)
- [API usage audit](docs/API_USAGE_AUDIT.md)

## Current limits

- Pixel-perfect reproduction of any provider's proprietary typography is out of scope; portable semantic structure is the contract.
- Images, embedded widgets, equations, comments, and provider-only interactive elements are excluded from v1.
- Microsoft Word is required for DOCX visual verification on Windows. Other platforms receive an honest structural-only result.
- Native destination smoke tests in signed-in Gmail, Notion, Google Docs, Word, and Outlook remain environment/user-session acceptance gates; automated tests do not claim those sessions were exercised.
- This repository does not yet declare an owner-approved distribution license.
- The HAI adapter files are complete on this side; registration in the separate HAI repository remains an owner-reviewed integration step.
