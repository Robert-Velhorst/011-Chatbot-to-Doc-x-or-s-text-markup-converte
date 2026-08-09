# Critical path

The product succeeds only when this complete chain works:

```text
source text or markup
  -> safe format detection and semantic parsing
  -> immutable local source version
  -> selected portable template
  -> DOCX/PDF/Markdown/text generation
  -> structural and visual verification where available
  -> real artifact download or checksum export
  -> correction creates a new version without changing the original
```

## Automated smoke

```powershell
.\.venv\Scripts\clean-paste-studio.exe convert fixtures\studio\sample-brief.md `
  --out work\critical-path `
  --formats docx,pdf,markdown,text
```

Expected evidence:

- four non-empty artifacts;
- DOCX opens as valid WordprocessingML and retains headings, lists, link, table, quote, and code;
- on Windows with Word, DOCX is exported to PDF and its first page is rendered non-blank;
- PDF has at least one page, extractable text, and a non-blank Poppler PNG;
- Markdown preserves semantic constructs;
- text contains a readable structural fallback.

## Browser smoke

1. Start `scripts/run-local.ps1`.
2. Open `http://127.0.0.1:8765`.
3. Edit the sample title/source and select formats.
4. Generate files.
5. Confirm the status changes from unsaved to saved only after the API succeeds.
6. Confirm DOCX/PDF verification rows show the returned status, not a hardcoded success.
7. Download an artifact and the export ZIP.
8. Correct the source and generate again; History must show the next version.
9. Delete a disposable project; it must disappear and its project directory must be removed.

## Clipboard smoke

1. Load `dist/chrome-extension` unpacked.
2. Copy an assistant response from a supported provider with headings, nested lists, table, link, and code.
3. Paste into a browser rich editor and a plain text field.
4. Confirm an unsupported page is unchanged unless that exact site was opted in.
5. Run the Windows companion and repeat into Word/Outlook. Confirm CF_HTML, RTF, and Unicode formats are present.

Signed-in third-party destination testing is manual because this repository does not own those accounts or sessions.
