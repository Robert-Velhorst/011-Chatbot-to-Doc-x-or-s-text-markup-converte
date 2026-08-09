# Windows companion

The companion is optional. It watches Windows clipboard-change notifications and acts only when the CF_HTML `SourceURL` belongs to a supported AI provider. It then writes Unicode text, CF_HTML, and RTF together for native applications.

It does not install a keyboard hook, poll the clipboard, retain clipboard history, log copied text, or make network calls.

The tray menu can pause/resume formatting, enable or disable per-user **Start with Windows**, and quit cleanly. Startup uses the current user's standard Windows Run key and requires no administrator rights.

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

Build the dependency-contained Windows folder from the repository root:

```powershell
.\scripts\build-companion.ps1
```

The executable is written to `dist\AI-Clean-Paste-Companion`.
