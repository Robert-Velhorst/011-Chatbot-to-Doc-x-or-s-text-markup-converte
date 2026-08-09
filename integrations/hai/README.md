# HAI connector

AI Clean Paste exposes a bounded connector for HAI. It accepts source text or markup and returns versioned document artifacts with SHA-256 checksums and authenticated download URLs.

## Boundary

- Authority is `artifact_generation_only`.
- The connector cannot send messages, modify Gmail/Drive, operate a browser, execute HAI workflows, or mutate any external provider.
- Every `/api/connectors/hai/v1/*` request requires the same bearer token as the production Studio API.
- Source content is stored only in the configured Studio data directory. It is never placed in access logs or telemetry.
- Use a stable `Idempotency-Key` per HAI conversion request so retries cannot create duplicate projects.

## Configure

1. Start Studio in production mode, locally or through the guarded ngrok script.
2. Store `CLEAN_PASTE_TOKEN` in HAI's approved local secret mechanism; do not paste it into source control or connector JSON.
3. Configure the base URL and routes from `openapi.yaml`.
4. Probe `GET /health`, then call the authenticated capabilities route.
5. Keep HAI's normal owner, provenance, review, and revocation controls around the returned artifact URLs.

Local base URL: `http://127.0.0.1:8765`
Remote base URL: the HTTPS forwarding URL printed by ngrok.

The included `hai-connector.example.json` contains no credential and is a setup template only; it is not a claim that the separate HAI repository has already registered the connector.
