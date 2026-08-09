from __future__ import annotations

import html
import re
from html.parser import HTMLParser
from typing import Iterable
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

ALLOWED = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote", "pre", "code", "strong", "b", "em", "i", "a", "table", "thead", "tbody", "tfoot", "tr", "th", "td", "br", "hr"}
DROP = {"script", "style", "button", "svg", "canvas", "img", "video", "audio", "iframe", "form", "input"}
VOID_DROP = {"img", "video", "audio", "input"}
BLOCK = {"p", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "li", "blockquote", "pre", "table", "tr", "hr"}


def clean_href(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme and parsed.scheme not in {"http", "https", "mailto"}:
        return None
    kept = [(key, item) for key, item in parse_qsl(parsed.query, keep_blank_values=True) if not re.match(r"^(utm_|ref$|ref_|source$|mc_)", key, re.I)]
    return urlunparse(parsed._replace(query=urlencode(kept)))


class SemanticHTML(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.output: list[str] = []
        self.stack: list[str | None] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs: Iterable[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self.skip_depth:
            self.skip_depth += 1
            self.stack.append(None)
            return
        if tag in VOID_DROP:
            return
        if tag in DROP or any("toolbar" in (value or "").lower() for key, value in attrs if key == "class"):
            self.skip_depth = 1
            self.stack.append(None)
            return
        if tag not in ALLOWED:
            self.stack.append(None)
            return
        tag = {"b": "strong", "i": "em"}.get(tag, tag)
        attribute = ""
        if tag == "a":
            href = dict(attrs).get("href")
            safe = clean_href(href) if href else None
            if safe:
                attribute = f' href="{html.escape(safe, quote=True)}"'
        self.output.append(f"<{tag}{attribute}>")
        self.stack.append(tag)

    def handle_startendtag(self, tag: str, attrs: Iterable[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)

    def handle_endtag(self, tag: str) -> None:
        if not self.stack:
            return
        opened = self.stack.pop()
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if opened and opened not in {"br", "hr"}:
            self.output.append(f"</{opened}>")

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        in_pre = "pre" in self.stack
        value = data if in_pre else re.sub(r"\s+", " ", data)
        if value:
            self.output.append(html.escape(value))


def normalize_html(source: str) -> str:
    parser = SemanticHTML()
    parser.feed(source)
    parser.close()
    result = "".join(parser.output)
    result = re.sub(r"<(p|li|td|th|blockquote)>\s*</\1>", "", result)
    return result.strip()


def plain_text(source_html: str) -> str:
    value = re.sub(r"<pre[^>]*>(.*?)</pre>", lambda match: "\n" + re.sub(r"<[^>]+>", "", match.group(1)) + "\n", source_html, flags=re.S | re.I)
    value = re.sub(r"</?(?:p|h[1-6]|ul|ol|blockquote|tr|table)[^>]*>", "\n", value, flags=re.I)
    value = re.sub(r"<li[^>]*>", "\n- ", value, flags=re.I)
    value = re.sub(r"</?(?:td|th)[^>]*>", "\t", value, flags=re.I)
    value = re.sub(r"<br\s*/?>", "\n", value, flags=re.I)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    return re.sub(r"\n{3,}", "\n\n", re.sub(r"[ \t]+\n", "\n", value)).strip()


def html_to_rtf(source_html: str) -> str:
    text = normalize_html(source_html)
    text = re.sub(r"<h[1-6][^>]*>(.*?)</h[1-6]>", lambda match: r"\\par\\b " + re.sub(r"<[^>]+>", "", match.group(1)) + r"\\b0\\par", text, flags=re.S | re.I)
    text = re.sub(r"<strong>(.*?)</strong>", r"\\b \1\\b0", text, flags=re.S | re.I)
    text = re.sub(r"<em>(.*?)</em>", r"\\i \1\\i0", text, flags=re.S | re.I)
    text = re.sub(r"<code>(.*?)</code>", r"\\f1 \1\\f0", text, flags=re.S | re.I)
    text = re.sub(r"<li[^>]*>", r"\\par\\bullet\\tab ", text, flags=re.I)
    text = re.sub(r"</?(?:p|ul|ol|blockquote|tr|table|tbody|thead|tfoot)[^>]*>", r"\\par ", text, flags=re.I)
    text = re.sub(r"</?(?:td|th)[^>]*>", r"\\tab ", text, flags=re.I)
    text = re.sub(r"<br\s*/?>", r"\\line ", text, flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    escaped = text.replace("\\", "\\\\").replace("{", "\\{").replace("}", "\\}")
    escaped = escaped.replace("\\\\par", "\\par").replace("\\\\tab", "\\tab").replace("\\\\b", "\\b").replace("\\\\i", "\\i").replace("\\\\f", "\\f").replace("\\\\bullet", "\\bullet").replace("\\\\line", "\\line")
    return r"{\rtf1\ansi\deff0{\fonttbl{\f0 Calibri;}{\f1 Consolas;}}" + escaped + "}"
