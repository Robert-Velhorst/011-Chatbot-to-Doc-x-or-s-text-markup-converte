# Windows 11 standalone guide

## Document Studio

1. Extract `AI-Clean-Paste-Studio-Windows-v0.2.0.zip` to a normal user-writable folder.
2. Double-click `AI-Clean-Paste-Studio.exe`.
3. The browser opens `http://127.0.0.1:8765` and a tray icon appears.
4. Use the tray menu to reopen or stop Studio.

Data is stored under `%LOCALAPPDATA%\AI Clean Paste\Studio`. The packaged folder contains Python and all required libraries; no developer runtime is required. Microsoft Word is used when installed to visually verify DOCX output.

If port 8765 is already in use, stop the other Studio instance before starting another. Windows SmartScreen may warn because this build is not code-signed; do not distribute it as a trusted signed installer until an owner-controlled signing certificate and release policy exist.

## Clipboard companion

1. Extract `AI-Clean-Paste-Companion-Windows-v0.2.0.zip`.
2. Double-click `AI-Clean-Paste-Companion.exe`.
3. Use its tray menu to pause/resume, enable per-user **Start with Windows**, or quit.

The companion never requires administrator rights, never installs a global keyboard hook, and never retains clipboard history.
