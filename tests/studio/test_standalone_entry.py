import sys

import pytest
from cleanpaste_studio import standalone, word_render_helper


def test_internal_renderer_dispatch_never_creates_server_or_tray(monkeypatch):
    received = []
    arguments = ["input.docx", "output.pdf", "owned.pid"]
    monkeypatch.setattr(sys, "argv", ["studio.exe", "-m", "cleanpaste_studio.word_render_helper", *arguments])
    monkeypatch.setattr(word_render_helper, "main", lambda values: received.extend(values) or 0)
    monkeypatch.setattr(standalone.uvicorn, "Server", lambda *_args, **_kwargs: pytest.fail("Server created in renderer mode"))
    with pytest.raises(SystemExit) as result:
        standalone.main()
    assert result.value.code == 0
    assert received == arguments


def test_arbitrary_module_and_unknown_arguments_are_rejected_before_startup(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["studio.exe", "-m", "untrusted_module"])
    monkeypatch.setattr(standalone.uvicorn, "Server", lambda *_args, **_kwargs: pytest.fail("Server created for unknown arguments"))
    with pytest.raises(SystemExit, match="Only --serve-only"):
        standalone.main()
