from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


root = Path(SPECPATH)
hidden = collect_submodules("clean_paste") + [
    "pystray._win32",
    "win32clipboard",
    "win32con",
    "win32gui",
]

analysis = Analysis(
    [str(root / "src" / "windows" / "main.py")],
    pathex=[str(root / "src" / "windows")],
    binaries=[],
    datas=[],
    hiddenimports=hidden,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "pytest", "ruff"],
    noarchive=False,
    optimize=1,
)

pyz = PYZ(analysis.pure)

exe = EXE(
    pyz,
    analysis.scripts,
    [],
    exclude_binaries=True,
    name="AI-Clean-Paste-Companion",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

collect = COLLECT(
    exe,
    analysis.binaries,
    analysis.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="AI-Clean-Paste-Companion",
)
