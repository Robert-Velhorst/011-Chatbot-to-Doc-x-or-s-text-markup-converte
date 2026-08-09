# Security, privacy, and threat model

## Trust boundary

The default deployment is a single-user application on loopback. The operating-system account and configured data directory are the ownership boundary. The product does not claim tenant isolation, team roles, internet exposure, or cloud processing.

## Threats and controls

| Threat | Control |
| --- | --- |
| Malicious copied HTML | allowlisted semantic parser; scripts, styles, forms, SVG, canvas, iframe, nav, and buttons ignored |
| Script links | only `http`, `https`, and `mailto` links survive |
| Path traversal | fixed-format project IDs, basename-only artifacts, resolved-parent containment checks |
| Accidental public server | loopback default; token mandatory for production or non-loopback host |
| Brute force / request flood | per-client in-memory request limit with `Retry-After` |
| Duplicate create/generate | validated `Idempotency-Key` cache scoped by operation |
| Oversized source | configurable byte ceiling, 2 MB default |
| Clipboard exfiltration | no network calls, history, polling, keyboard hook, or content logs |
| Content in audit trails | event metadata only; dedicated negative test |
| Browser injection | strict CSP, frame denial, no CDN/runtime remote code |
| Artifact ambiguity | SHA-256 and byte size stored; export manifest signed by hashes (not a cryptographic identity signature) |
| Fake verification | three-state result and exact reason; structural-only is not labeled visual success |

## Credentials

`CLEAN_PASTE_TOKEN` is the only application secret. It is read from the environment and must never be committed. The browser submits it once to `/api/session`; the server returns a cryptographically random, HTTP-only, SameSite Strict session value. Sessions expire after eight hours, exist only in server memory, can be revoked through logout, and become invalid whenever the process restarts. Neither the raw token nor the session value is written to local storage or application logs.

If the token is exposed, stop the server, generate a new random value, update the local environment/secret manager, and restart. Restarting immediately invalidates every in-memory browser session.

ngrok does not weaken this boundary: production mode and the token remain mandatory, Studio stays on loopback, and only `/health` is public without authentication. The HAI connector has `artifact_generation_only` authority and cannot operate browsers, providers, Gmail, Drive, messages, or HAI workflows.

## Privacy impact assessment

Data categories are source documents, project titles, generated files, template choice, version metadata, checksums, and metadata-only audit events. Processing purpose is local document conversion. Retention is user-controlled until project deletion or data-directory removal. There is no telemetry or third-party subprocessor. Export is explicit and local. Deletion removes database rows and the project directory; storage-device forensic recovery is outside application control.

## Security headers

Responses set `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, a restrictive Permissions Policy, and a self-only CSP. API responses are `no-store`.

## Reporting

Do not include private source text in a bug report. Use commands, version, verification status/reason, and sanitized metadata. A content-free support bundle is a roadmap item rather than a hidden automatic upload.
