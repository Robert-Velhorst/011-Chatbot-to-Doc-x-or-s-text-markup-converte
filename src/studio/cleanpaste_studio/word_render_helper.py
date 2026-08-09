from __future__ import annotations

import sys
from pathlib import Path


def render(input_path: Path, output_path: Path, pid_path: Path) -> None:
    import pythoncom
    import win32com.client

    def word_pids() -> set[int]:
        wmi = win32com.client.GetObject("winmgmts:")
        return {
            int(process.ProcessId)
            for process in wmi.ExecQuery(
                "SELECT ProcessId FROM Win32_Process WHERE Name='WINWORD.EXE'"
            )
        }

    word = None
    document = None
    pythoncom.CoInitialize()
    try:
        before = word_pids()
        word = win32com.client.DispatchEx("Word.Application")
        word.Visible = False
        word.DisplayAlerts = 0
        word.AutomationSecurity = 3
        created = word_pids() - before
        if len(created) == 1:
            pid_path.write_text(str(created.pop()), encoding="ascii")
        document = word.Documents.Open(
            str(input_path.resolve()),
            ConfirmConversions=False,
            ReadOnly=True,
            AddToRecentFiles=False,
            NoEncodingDialog=True,
            OpenAndRepair=False,
        )
        document.ExportAsFixedFormat(
            str(output_path.resolve()),
            17,
            OpenAfterExport=False,
            OptimizeFor=0,
            CreateBookmarks=1,
        )
    finally:
        if document is not None:
            document.Close(False)
        if word is not None:
            word.Quit()
        pythoncom.CoUninitialize()


def main(argv: list[str] | None = None) -> int:
    args = argv or sys.argv[1:]
    if len(args) != 3:
        print("Usage: word_render_helper INPUT.docx OUTPUT.pdf PIDFILE", file=sys.stderr)
        return 2
    try:
        render(Path(args[0]), Path(args[1]), Path(args[2]))
    except Exception as exc:  # noqa: BLE001 - isolated renderer reports failure to parent
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
