from __future__ import annotations

import json
from pathlib import Path

from clean_paste.agent import is_supported_source
from clean_paste.cf_html import build_cf_html, parse_cf_html
from clean_paste.normalizer import html_to_rtf, normalize_html, plain_text
from clean_paste.startup import RUN_KEY, launch_command


FIXTURES = json.loads((Path(__file__).parents[1] / "fixtures" / "normalization.json").read_text(encoding="utf-8"))


def test_cf_html_round_trip() -> None:
    raw = build_cf_html("<p>Hello</p>", "https://chatgpt.com/c/test")
    assert parse_cf_html(raw) == ("https://chatgpt.com/c/test", "<p>Hello</p>")


def test_only_supported_sources_are_automatic() -> None:
    assert is_supported_source("https://chatgpt.com/c/test")
    assert is_supported_source("https://www.perplexity.ai/search?q=x")
    assert not is_supported_source("https://example.com/article")


def test_shared_normalization_fixtures() -> None:
    for fixture in FIXTURES:
        result = normalize_html(fixture["html"])
        assert "script" not in result.lower()
        assert "button" not in result.lower()
        text = plain_text(result)
        for fragment in fixture["plainTextIncludes"]:
            assert fragment in text
        rtf = html_to_rtf(result)
        for fragment in fixture["rtfIncludes"]:
            assert fragment in rtf


def test_startup_uses_current_user_run_key_and_exact_launcher() -> None:
    assert RUN_KEY == r"Software\Microsoft\Windows\CurrentVersion\Run"
    command = launch_command()
    assert "python" in command.lower()
    assert "main.py" in command.lower()
