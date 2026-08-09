from __future__ import annotations

import subprocess
import sys
import winreg
from pathlib import Path

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
VALUE_NAME = "AI Clean Paste Clipboard"


def launch_command() -> str:
    executable = Path(sys.executable).resolve()
    if getattr(sys, "frozen", False):
        return subprocess.list2cmdline([str(executable)])
    main_script = Path(__file__).resolve().parents[1] / "main.py"
    return subprocess.list2cmdline([str(executable), str(main_script)])


def startup_enabled() -> bool:
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            value, _value_type = winreg.QueryValueEx(key, VALUE_NAME)
        return value == launch_command()
    except FileNotFoundError:
        return False


def set_startup(enabled: bool) -> None:
    with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, RUN_KEY, access=winreg.KEY_SET_VALUE) as key:
        if enabled:
            winreg.SetValueEx(key, VALUE_NAME, 0, winreg.REG_SZ, launch_command())
        else:
            try:
                winreg.DeleteValue(key, VALUE_NAME)
            except FileNotFoundError:
                pass
