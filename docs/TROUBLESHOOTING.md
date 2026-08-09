# Troubleshooting and error catalog

| Symptom | Meaning | Action |
| --- | --- | --- |
| `Authentication required` | token mode is active | unlock with the configured local token |
| `Invalid local access token` | token mismatch | verify environment value; do not paste it into logs/issues |
| `Source document exceeds...` | byte ceiling exceeded | split the document or intentionally raise the local limit |
| `Rate limit exceeded` | more than configured requests/minute | wait 60 seconds; check for loops |
| DOCX `Structural` | Word visual renderer unavailable/failed | install/repair Word on Windows or inspect manually |
| PDF `Failed` | PDF parse/render/non-blank check failed | preserve source and reason; do not distribute as verified |
| Browser copy unchanged | unsupported/disabled source or selection outside assistant response | enable provider; select response content; generic support is per-site opt-in |
| Native paste is plain | companion disabled or SourceURL not recognized | enable tray companion and copy from supported source page |
| UI says it is not built | Vite output missing | run `npm.cmd run studio:build` |
| Database error | runtime data inconsistency/lock | stop app, backup directory, inspect a copy; do not delete blindly |

Run `clean-paste-studio doctor` for Python version, renderer lookup, and data-directory write access.
