# Final verification report

Date: 2026-08-09
Release: 0.2.0
Source specification: 124-page Giant Codex Goal Prompt

## Outcome

The repository now contains three real local-first product surfaces plus deployment and integration boundaries:

- Chrome MV3 source-side copy normalization for seven explicit AI providers and opt-in generic sites;
- Windows clipboard-notification companion writing Unicode, CF_HTML, and RTF without polling or key interception;
- Document Studio with React UI, FastAPI, SQLite/versioned source storage, four templates, DOCX/PDF/Markdown/text generators, checksums, export packages, corrections, verification, CLI, Windows standalone, and Docker;
- token-authenticated, idempotent HAI artifact-generation connector plus OpenAPI contract;
- guarded production-mode ngrok launcher.

The local product is implemented and verified. It is not represented as a signed/store-distributed or universally accepted cloud service.

## Starting state and traceability

- The workspace was not a Git worktree and the canonical GitHub repository was empty: no starting commit, default branch, or remote refs.
- Existing extension/companion source and fixtures were retained and audited rather than replaced.
- All 124 PDF pages were extracted and visually inspected in contact sheets. The 116 phase rows are mapped in `GOAL_COMPLETION_MATRIX.md`.
- N/A phases describe deliberately absent SaaS/team/billing/provider-mutation systems. Partial rows remain visible and are not counted as complete.

## Automated gates

| Gate | Result |
| --- | --- |
| Python formatting/lint | Ruff clean |
| Python tests | 20 passed; one upstream Starlette `TestClient` deprecation warning |
| TypeScript | both extension and Studio type checks passed |
| Extension tests | 6 passed across provider, normalizer, and copy-event suites |
| Extension build | MV3 package built successfully |
| Studio build | Vite production bundle built; 214.48 kB JS / 68.04 kB gzip and 12.61 kB CSS / 3.59 kB gzip |
| JavaScript dependencies | `npm audit --omit=dev`: 0 vulnerabilities after upgrading transitive `nanoid` to 3.3.18 |
| Python dependencies | `pip check`: no broken requirements |
| CLI verification | doctor and PDF/Markdown/text fixture conversion passed |
| Docker | image built; container reached `healthy`; `/health` returned `ok`; authenticated HAI boundary returned `artifact_generation_only` |

The PowerShell gates explicitly convert every nonzero native exit code into a script failure. This was added after the audit proved `$ErrorActionPreference` alone did not stop on a Ruff failure.

## Windows 11 standalone evidence

Host: Windows 11 build 26200, Python 3.12.13 build environment.

| Package | Runtime evidence |
| --- | --- |
| Document Studio | release executable started; `/health` = `ok`; UI = HTTP 200 with title `AI Clean Paste — Document Studio`; HAI authority correct; 96.6 MB working set / 64 MB private in smoke; folder 58.6 MB |
| Clipboard companion | release executable remained responsive; 34.6 MB working set; folder 35.2 MB; tray-backed listener owns its window/message loop thread |

The Studio tray exposes Open and Stop. The companion tray exposes enable/pause, per-user Start with Windows, and Quit. Startup uses HKCU and requires no elevation. Executables are dependency-contained folders, not code-signed installers.

## Browser and visual evidence

The in-app browser completed the real local flow: load sample, create project, generate all four formats, wait for the backend, download/export, open History, create correction/version 2, visit Templates and Settings, and observe no console warnings or errors. DOCX and PDF showed verified one-page results.

The browser plugin produced tiled screenshots on this host, so Playwright CLI was used only as the screenshot fallback after functional verification. Evidence:

- `work/browser-qa/playwright-final.png` — 1586×992 final generated state;
- `work/browser-qa/playwright-mobile.png` — 390×844 responsive state with no page overflow;
- `docs/design/document-studio-concept.png` — 1586×992 approved concept reference.

Fidelity ledger:

1. exact three-column desktop composition at the concept viewport;
2. matching white canvas, navy navigation, cobalt actions, and green verification semantics;
3. matching Studio, Templates, History, Settings, format, and Generate workflow labels;
4. matching editor/inspector density, borders, radii, and status hierarchy;
5. mobile collapses to one column without horizontal page overflow.

Intentional deviations are real project/history data instead of fake five-row content, real file sizes/page counts, a native editable textarea instead of decorative syntax coloring, and functional success/export feedback.

## Render verification and bug findings

Human inspection found and fixed duplicated titles, flattened PDF nested-list markers, escaped code quotes, and a Word-render timeout/leaked-command failure. The current PDF and Word-rendered DOCX samples each show one title, nested lists, link, blockquote, table, and clean code on one page.

The document-skill LibreOffice renderer was attempted but LibreOffice is absent (`WinError 2`). The product's isolated Microsoft Word renderer succeeded instead. It records and may terminate only the exact `WINWORD` process created through `DispatchEx`; concurrent Word renders are serialized to protect resources.

## Performance and resource controls

- One semantic parse is reused across all requested formats.
- SQLite uses WAL, `synchronous=NORMAL`, bounded reads, and indexes for project recency and artifact versions.
- API source size defaults to 2 MB; project lists cap at 100; rate limiting defaults to 60 requests/minute/client.
- Word visual verification is serialized; there is no idle worker/scheduler or clipboard polling loop.
- 30 sample Markdown+text project conversions: p50 175.97 ms, p95 388.26 ms, max 663.86 ms on the concurrently loaded host.

## Privacy and security evidence

- Session cookies are random, HTTP-only, SameSite Strict, memory-only, expiring, revocable, and invalid after restart.
- Production/non-loopback startup without a token fails closed.
- HAI endpoints require bearer auth, validate size and idempotency keys, and expose `artifact_generation_only` authority.
- No telemetry, content logger, clipboard history, global keyboard hook, remote runtime code, provider credentials, or Gmail/Drive permission exists.
- Audit rows contain only event type, project ID, version, and timestamp.
- Path traversal, malformed input, unsafe links/UI markup, size limits, auth, deletion, idempotency, and negative privacy behavior are covered by tests.

## ngrok evidence and genuine external gate

ngrok 3.39.8 is installed and its configuration validates. The smoke reached ngrok but a separate long-running LARO endpoint already occupies the account's assigned endpoint. ngrok rejected a second endpoint with `ERR_NGROK_334`. The existing tunnel was preserved; pooling was refused because it would mix unrelated traffic.

`scripts/run-ngrok.ps1` is implemented and forces production mode, loopback binding, and a strong token. A simultaneous public acceptance run requires intentionally stopping the other endpoint or adding account endpoint capacity. This is an external account-state blocker, not an application fallback.

## Release packages and checksums

`scripts/package-release.ps1` produces five versioned ZIPs and `outputs/SHA256SUMS.txt`:

- Chrome extension;
- Windows clipboard companion;
- Windows Document Studio;
- HAI connector contract;
- complete source release.

Hashes are generated after final builds and are the authoritative package-integrity record.

## Remaining manual/external gates

- authenticated paste smoke tests in user-owned Gmail, Notion, Google Docs, Word, and Outlook sessions;
- deliberate HAI registration in the separate HAI repository with owner/review/provenance controls;
- a free/additional ngrok endpoint for simultaneous live public acceptance;
- owner-selected license, code-signing certificate, signed installer/store submission, and release policy;
- non-Windows DOCX visual rendering (structural-only status remains explicit there);
- deferred search/cursor pagination, large-dataset SLO campaign, UI localization, and support-bundle command.

No copied content, Google data, or provider account was accessed merely to claim these external gates passed.
