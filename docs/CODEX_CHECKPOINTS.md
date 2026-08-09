# Codex checkpoints

| Checkpoint | State | Resume evidence |
| --- | --- | --- |
| Supplied code audited | complete | `TECHNICAL_AUDIT.md` |
| Product contract fixed | complete | `CRITICAL_PATH.md` |
| Conversion core | complete | `src/studio/cleanpaste_studio` |
| Local persistence/security | complete | `storage.py`, `security.py`, API tests |
| UI implementation | complete and browser-verified | `studio-ui`, concept PNG, final report |
| Unit/integration gates | complete | 6 Vitest plus 21 Python tests |
| DOCX/PDF render proof | complete for sample | `work/studio-smoke-v2`, final report |
| Browser core workflow | complete | final report and browser QA evidence |
| Windows/Docker packaging | complete and smoke-tested | `dist`, final report |
| HAI/ngrok | connector complete; live ngrok externally gated | `integrations/hai`, `docs/NGROK.md`, final report |
| Packaging | complete; all ZIP integrity checks and SHA-256 match | `outputs/SHA256SUMS.txt` |
| Git commit/push | complete; canonical `main` pushed and GitHub quality workflow green | final report |

Resume by running `scripts/verify.ps1`, `scripts/smoke-standalone.ps1`, and inspecting `outputs/SHA256SUMS.txt`. Never infer completion from package existence alone.
