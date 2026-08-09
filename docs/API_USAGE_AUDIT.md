# API usage audit

## Endpoints

| Method/path | UI/CLI consumer | Side effect | Guard |
| --- | --- | --- | --- |
| `GET /health` | operator/healthcheck | none | public, no content |
| `GET /readiness` | operator | none | public, configuration only |
| `POST /api/session` | unlock dialog | sets HTTP-only cookie | rate limited; token comparison |
| `DELETE /api/session` | available API logout | clears cookie | authenticated when token configured |
| `GET /api/templates` | Studio inspector/templates | none | auth/rate limit |
| `GET /api/projects` | sidebar/history | none | auth/rate limit; max 100 |
| `POST /api/projects` | first generation | writes project/version/source | size, parser, token, rate, optional idempotency |
| `GET /api/projects/{id}` | operator/API | none | validated ID |
| `GET /api/projects/{id}/source` | open document | returns selected local source | validated ID/version |
| `POST /api/projects/{id}/versions` | correction | immutable new source version | size, parser, ownership boundary |
| `POST /api/projects/{id}/generate` | Generate files | writes selected artifacts and verification | format/template validation, optional idempotency |
| `GET .../artifacts/{name}` | file row | none | project/version/basename containment |
| `POST /api/projects/{id}/export` | Export | writes/returns ZIP | project/version containment |
| `DELETE /api/projects/{id}` | History delete | deletes rows/tree | confirmation in UI, ID validation |
| `GET /api/privacy` | diagnostics | none | metadata-only counts |
| `GET /api/connectors/hai/v1/capabilities` | HAI/operator | none | bearer/session auth; bounded authority metadata |
| `POST /api/connectors/hai/v1/convert` | HAI | writes one versioned project and artifacts | token, rate, size, parser, template, format, idempotency |

## Error contract

FastAPI returns JSON `{ "detail": ... }` with meaningful 4xx codes. The UI displays `detail`. Missing resources return 404, validation errors 422, oversized sources 413, authentication failures 401, and rate limiting 429 with `Retry-After: 60`.

## Unused/dead endpoints

No endpoint exists solely for a fake UI state. `GET /api/projects/{id}` and session deletion are currently API/operator surfaces rather than primary UI calls; both are intentional and tested through the shared storage/security boundaries.

## External APIs

There are no outbound application APIs. Provider names in the extension are DOM/source adapters, not remote API integrations. HAI calls Studio inbound through the checked-in contract. The product does not require an OpenAI, Anthropic, Google, Microsoft, Perplexity, xAI, or Manus key.
