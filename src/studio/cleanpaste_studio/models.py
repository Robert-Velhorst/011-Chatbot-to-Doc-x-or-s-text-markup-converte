from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

BlockKind = Literal[
    "heading",
    "paragraph",
    "list_item",
    "blockquote",
    "code",
    "table",
    "horizontal_rule",
]


@dataclass(slots=True)
class InlineSpan:
    text: str
    bold: bool = False
    italic: bool = False
    code: bool = False
    href: str | None = None


@dataclass(slots=True)
class Block:
    kind: BlockKind
    spans: list[InlineSpan] = field(default_factory=list)
    level: int = 0
    ordered: bool = False
    language: str | None = None
    rows: list[list[str]] = field(default_factory=list)

    @property
    def text(self) -> str:
        return "".join(span.text for span in self.spans)


@dataclass(slots=True)
class ParsedDocument:
    title: str
    source_format: str
    source_hash: str
    blocks: list[Block]

    def as_dict(self) -> dict:
        return asdict(self)


@dataclass(slots=True)
class VerificationResult:
    artifact: str
    status: Literal["verified", "unverified", "failed"]
    page_count: int | None
    checks: list[str]
    reason: str | None = None
    preview_path: Path | None = None

    def as_dict(self) -> dict:
        data = asdict(self)
        if self.preview_path:
            data["preview_path"] = self.preview_path.name
        return data


@dataclass(slots=True)
class GeneratedArtifact:
    format: str
    path: Path
    sha256: str
    size: int
    verification: VerificationResult | None = None

    def as_dict(self) -> dict:
        return {
            "format": self.format,
            "name": self.path.name,
            "sha256": self.sha256,
            "size": self.size,
            "verification": self.verification.as_dict() if self.verification else None,
        }
