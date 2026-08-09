from __future__ import annotations

import hashlib
import re
from html.parser import HTMLParser
from typing import ClassVar
from urllib.parse import urlparse

from markdown_it import MarkdownIt
from markdown_it.token import Token

from .models import Block, InlineSpan, ParsedDocument

SAFE_SCHEMES = {"http", "https", "mailto"}


def _safe_href(value: str | None) -> str | None:
    if not value:
        return None
    parsed = urlparse(value.strip())
    return value.strip() if parsed.scheme.lower() in SAFE_SCHEMES else None


def _merge_spans(spans: list[InlineSpan]) -> list[InlineSpan]:
    merged: list[InlineSpan] = []
    for span in spans:
        if not span.text:
            continue
        if merged and (
            merged[-1].bold,
            merged[-1].italic,
            merged[-1].code,
            merged[-1].href,
        ) == (span.bold, span.italic, span.code, span.href):
            merged[-1].text += span.text
        else:
            merged.append(span)
    return merged


def _inline_spans(token: Token) -> list[InlineSpan]:
    spans: list[InlineSpan] = []
    bold = italic = False
    href: str | None = None
    for child in token.children or []:
        if child.type == "strong_open":
            bold = True
        elif child.type == "strong_close":
            bold = False
        elif child.type == "em_open":
            italic = True
        elif child.type == "em_close":
            italic = False
        elif child.type == "link_open":
            href = _safe_href(child.attrGet("href"))
        elif child.type == "link_close":
            href = None
        elif child.type in {"softbreak", "hardbreak"}:
            spans.append(InlineSpan("\n", bold=bold, italic=italic, href=href))
        elif child.type == "code_inline":
            spans.append(InlineSpan(child.content, code=True, href=href))
        elif child.type in {"text", "html_inline"}:
            text = re.sub(r"<[^>]+>", "", child.content)
            spans.append(InlineSpan(text, bold=bold, italic=italic, href=href))
    return _merge_spans(spans)


class SemanticHTMLParser(HTMLParser):
    ignored: ClassVar[set[str]] = {
        "script",
        "style",
        "svg",
        "canvas",
        "button",
        "nav",
        "form",
        "iframe",
    }

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.blocks: list[Block] = []
        self.skip_depth = 0
        self.current: Block | None = None
        self.bold = False
        self.italic = False
        self.code = False
        self.href: str | None = None
        self.list_stack: list[bool] = []
        self.table_rows: list[list[str]] = []
        self.row: list[str] | None = None
        self.cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        tag = tag.lower()
        if self.skip_depth:
            self.skip_depth += 1
            return
        if tag in self.ignored:
            self.skip_depth = 1
            return
        values = dict(attrs)
        if tag in {"strong", "b"}:
            self.bold = True
        elif tag in {"em", "i"}:
            self.italic = True
        elif tag == "a":
            self.href = _safe_href(values.get("href"))
        elif tag in {"ul", "ol"}:
            self.list_stack.append(tag == "ol")
        elif tag == "li":
            self.current = Block(
                "list_item", level=max(0, len(self.list_stack) - 1), ordered=self.list_stack[-1]
            )
        elif re.fullmatch(r"h[1-6]", tag):
            self.current = Block("heading", level=int(tag[1]))
        elif tag == "p":
            self.current = Block("paragraph")
        elif tag == "blockquote":
            self.current = Block("blockquote")
        elif tag == "pre":
            self.current = Block("code")
            self.code = True
        elif tag == "code":
            self.code = True
        elif tag == "hr":
            self.blocks.append(Block("horizontal_rule"))
        elif tag == "br" and self.current:
            self.current.spans.append(InlineSpan("\n"))
        elif tag == "table":
            self.table_rows = []
        elif tag == "tr":
            self.row = []
        elif tag in {"td", "th"}:
            self.cell = []

    def handle_endtag(self, tag: str) -> None:
        tag = tag.lower()
        if self.skip_depth:
            self.skip_depth -= 1
            return
        if tag in {"strong", "b"}:
            self.bold = False
        elif tag in {"em", "i"}:
            self.italic = False
        elif tag == "a":
            self.href = None
        elif tag in {"ul", "ol"} and self.list_stack:
            self.list_stack.pop()
        elif tag in {"li", "p", "blockquote", "pre"} or re.fullmatch(r"h[1-6]", tag):
            self._finish_current()
            if tag == "pre":
                self.code = False
        elif tag == "code":
            self.code = False
        elif tag in {"td", "th"} and self.cell is not None and self.row is not None:
            self.row.append("".join(self.cell).strip())
            self.cell = None
        elif tag == "tr" and self.row is not None:
            if self.row:
                self.table_rows.append(self.row)
            self.row = None
        elif tag == "table":
            if self.table_rows:
                self.blocks.append(Block("table", rows=self.table_rows))
            self.table_rows = []

    def handle_data(self, data: str) -> None:
        if self.skip_depth:
            return
        if self.cell is not None:
            self.cell.append(data)
        if self.current:
            self.current.spans.append(
                InlineSpan(data, bold=self.bold, italic=self.italic, code=self.code, href=self.href)
            )

    def _finish_current(self) -> None:
        if self.current:
            self.current.spans = _merge_spans(self.current.spans)
            if self.current.text.strip():
                self.blocks.append(self.current)
        self.current = None

    def finish(self) -> list[Block]:
        self._finish_current()
        return self.blocks


def detect_format(source: str) -> str:
    if re.search(
        r"</?(?:h[1-6]|p|ul|ol|li|table|blockquote|pre|strong|a)\b", source, re.IGNORECASE
    ):
        return "html"
    if re.search(r"(^|\n)\s{0,3}(#{1,6}\s|[-*+]\s|\d+[.)]\s|```|>\s|\|.+\|)", source):
        return "markdown"
    return "plain"


def parse_markdown(source: str) -> list[Block]:
    md = MarkdownIt("commonmark", {"html": False}).enable("table")
    tokens = md.parse(source)
    blocks: list[Block] = []
    list_stack: list[bool] = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token.type in {"bullet_list_open", "ordered_list_open"}:
            list_stack.append(token.type == "ordered_list_open")
        elif token.type in {"bullet_list_close", "ordered_list_close"} and list_stack:
            list_stack.pop()
        elif token.type == "heading_open" and i + 1 < len(tokens):
            level = int(token.tag[1])
            blocks.append(Block("heading", _inline_spans(tokens[i + 1]), level=level))
        elif token.type == "paragraph_open" and i + 1 < len(tokens):
            spans = _inline_spans(tokens[i + 1])
            if spans:
                if list_stack:
                    blocks.append(
                        Block(
                            "list_item",
                            spans,
                            level=max(0, len(list_stack) - 1),
                            ordered=list_stack[-1],
                        )
                    )
                elif i > 0 and tokens[i - 1].type == "blockquote_open":
                    blocks.append(Block("blockquote", spans))
                else:
                    blocks.append(Block("paragraph", spans))
        elif token.type in {"fence", "code_block"}:
            blocks.append(
                Block(
                    "code",
                    [InlineSpan(token.content.rstrip("\n"), code=True)],
                    language=token.info or None,
                )
            )
        elif token.type == "hr":
            blocks.append(Block("horizontal_rule"))
        elif token.type == "table_open":
            rows: list[list[str]] = []
            row: list[str] = []
            i += 1
            while i < len(tokens) and tokens[i].type != "table_close":
                current = tokens[i]
                if current.type == "tr_open":
                    row = []
                elif current.type == "inline":
                    row.append(current.content.strip())
                elif current.type == "tr_close" and row:
                    rows.append(row)
                i += 1
            if rows:
                blocks.append(Block("table", rows=rows))
        i += 1
    return blocks


def parse_html(source: str) -> list[Block]:
    parser = SemanticHTMLParser()
    parser.feed(source)
    parser.close()
    return parser.finish()


def parse_plain(source: str) -> list[Block]:
    blocks: list[Block] = []
    for part in re.split(r"\n\s*\n", source.strip()):
        text = part.strip()
        if text:
            blocks.append(Block("paragraph", [InlineSpan(text)]))
    return blocks


def parse_document(
    source: str, title: str = "Untitled document", source_format: str = "auto"
) -> ParsedDocument:
    source_format = detect_format(source) if source_format == "auto" else source_format.lower()
    if source_format not in {"markdown", "html", "plain"}:
        raise ValueError(f"Unsupported source format: {source_format}")
    blocks = {
        "markdown": parse_markdown,
        "html": parse_html,
        "plain": parse_plain,
    }[source_format](source)
    if not blocks and source.strip():
        blocks = parse_plain(source)
    return ParsedDocument(
        title=title.strip() or "Untitled document",
        source_format=source_format,
        source_hash=hashlib.sha256(source.encode("utf-8")).hexdigest(),
        blocks=blocks,
    )
