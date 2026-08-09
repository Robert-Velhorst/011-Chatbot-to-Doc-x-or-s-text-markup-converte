# Acceptance tests

## Automated acceptance matrix

| ID | Scenario | Expected result | Automated evidence |
| --- | --- | --- | --- |
| A01 | Detect Markdown, HTML, plain text | correct parser selected | `test_parser.py` |
| A02 | Markdown headings/lists/table/code/link | semantic blocks retained | `test_markdown_structure_and_safe_links` |
| A03 | Provider UI/script markup | removed | `test_html_removes_unsafe_ui_and_preserves_semantics` |
| A04 | Unsafe link scheme | link target removed | parser test |
| A05 | Generate DOCX | valid package, text, table, metadata | `test_all_generators_create_portable_files` |
| A06 | Generate PDF | valid non-empty page | generator and verifier tests |
| A07 | Generate Markdown/text | readable semantic fallback | generator test |
| A08 | Render PDF | non-blank PNG | `test_pdf_verifier_renders_a_non_blank_preview` |
| A09 | Correct a document | new immutable version | `test_versioning_export_and_deletion` |
| A10 | Export package | source/artifacts plus checksums | storage test |
| A11 | Delete project | rows and directory removed | storage test |
| A12 | Traverse project/artifact path | rejected | `test_path_traversal_is_rejected` |
| A13 | Audit event privacy | no title/source/URL/hash | audit test |
| A14 | API critical path | create/generate/download/export | `test_critical_api_path` |
| A15 | Production without token | startup fails | API security test |
| A16 | Oversized source | HTTP 413 | API security test |
| A17 | Duplicate create with idempotency key | one project | idempotency test |
| A18 | Supported provider copy | sanitized HTML/text written synchronously | `copy-event.test.ts` |
| A19 | Unsupported browser copy | unchanged | `copy-event.test.ts` |
| A20 | Windows CF_HTML/RTF/text payload | formats parse and serialize | `test_windows.py` |
| A21 | HAI convert/capabilities | token, authority, idempotency, size/key validation | `test_hai_connector_is_authenticated_bounded_and_idempotent` |
| A22 | Windows startup contract | exact per-user launcher command | `test_startup_uses_current_user_run_key_and_exact_launcher` |

## Manual acceptance matrix

These require an interactive browser or user-owned third-party account and must not be inferred from unit tests.

| ID | Environment | Flow | Pass evidence |
| --- | --- | --- | --- |
| M01 | Desktop browser | Studio edit -> generate -> download | visible verified files and successful downloads |
| M02 | 390px viewport | Studio navigation, editor, inspector | no horizontal page overflow or clipped primary action |
| M03 | Chrome supported AI source | copy -> Gmail/Notion/Docs-like rich editor | headings/lists/table/code remain semantic |
| M04 | Chrome text input | copy -> plain field | structured readable text |
| M05 | Unsupported site | normal copy | clipboard unchanged until explicit opt-in |
| M06 | Word | supported-source copy with tray companion | Word receives rich structure |
| M07 | Outlook | supported-source copy with tray companion | Outlook receives rich structure |
| M08 | Delete | disposable project removal | project and its files no longer accessible |
| M09 | Windows standalone | launch -> browser/UI/health -> tray stop | packaged process and health evidence |
| M10 | ngrok | production token -> public health/auth boundary | external endpoint available; never pooled with unrelated tunnel |
| M11 | HAI | owner registers OpenAPI connector -> bounded conversion | owner/provenance/review controls retained in separate HAI deployment |

## Failure acceptance

- If Word is missing, DOCX must show `unverified` with the exact reason.
- If Poppler fails, PDF must show `failed` or `unverified`; no green verified label.
- If the API fails, the UI must remain unsaved and show the returned error.
- If token authentication is enabled, API content must remain inaccessible until unlock succeeds.
- A malformed source may degrade to readable paragraphs, but must not execute markup or escape storage boundaries.
