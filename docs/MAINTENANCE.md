# Maintenance, release, and roadmap

## Release gate

1. Run `scripts/verify.ps1`.
2. Run the desktop and mobile browser critical path.
3. Render and inspect the sample DOCX/PDF.
4. Rebuild packages; inspect their file lists and hashes.
5. Confirm Git contains no runtime DB, environment, upload, private source, or secret.
6. Update `FINAL_VERIFICATION_REPORT.md` and changelog.

## Versioning

Use semantic versioning. The extension, Windows companion, and Studio can be versioned independently in release notes even when shipped in one source package. Any schema change requires a new ordered migration and pre-migration backup instructions.

## Blocked/deferred roadmap

- signed-in Gmail/Notion/Google Docs/Word/Outlook acceptance runs;
- cross-platform DOCX renderer (LibreOffice service) with visual parity checks;
- async job queue only if measured document sizes justify it;
- search/cursor pagination for large project collections;
- Dutch interface localization;
- sanitized support-bundle command;
- owner decision on distribution license;
- signed Windows installer and extension-store submission.

No deferred item is represented by an enabled fake control.
