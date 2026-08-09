from pathlib import Path

from PyInstaller.utils.hooks import collect_submodules


root = Path(SPECPATH)
hidden = collect_submodules("cleanpaste_studio") + [
    "win32com.client",
    "pythoncom",
    "pywintypes",
    "win32timezone",
]

analysis = Analysis(
    [str(root / "src" / "studio" / "cleanpaste_studio" / "standalone.py")],
    pathex=[str(root / "src" / "studio")],
    binaries=[],
    datas=[(str(root / "studio-ui" / "dist"), "studio-ui/dist")],
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
    name="AI-Clean-Paste-Studio",
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
    name="AI-Clean-Paste-Studio",
)
