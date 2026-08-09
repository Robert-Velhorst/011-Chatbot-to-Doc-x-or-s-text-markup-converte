from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass(frozen=True, slots=True)
class TemplateProfile:
    id: str
    name: str
    description: str
    page_size: str
    margin_inches: float
    body_font: str
    heading_font: str
    mono_font: str
    body_size: float
    line_spacing: float
    accent: str
    text: str
    muted: str
    compact: bool = False

    def as_dict(self) -> dict:
        return asdict(self)


PROFILES: dict[str, TemplateProfile] = {
    "standard_business_brief": TemplateProfile(
        id="standard_business_brief",
        name="Standard business brief",
        description="Polished reports and proposals with restrained hierarchy.",
        page_size="letter",
        margin_inches=0.78,
        body_font="Aptos",
        heading_font="Aptos Display",
        mono_font="Consolas",
        body_size=10.5,
        line_spacing=1.12,
        accent="#1456D9",
        text="#172033",
        muted="#5E6B7E",
    ),
    "google_docs_default": TemplateProfile(
        id="google_docs_default",
        name="Google Docs default",
        description="Portable Arial-based document styling for collaborative editors.",
        page_size="letter",
        margin_inches=1.0,
        body_font="Arial",
        heading_font="Arial",
        mono_font="Courier New",
        body_size=11,
        line_spacing=1.15,
        accent="#1A73E8",
        text="#202124",
        muted="#5F6368",
    ),
    "compact_reference_guide": TemplateProfile(
        id="compact_reference_guide",
        name="Compact reference guide",
        description="Dense but readable instructions, checklists, and technical notes.",
        page_size="letter",
        margin_inches=0.62,
        body_font="Arial",
        heading_font="Arial",
        mono_font="Consolas",
        body_size=9.5,
        line_spacing=1.02,
        accent="#0F6B55",
        text="#17201D",
        muted="#5A6863",
        compact=True,
    ),
    "narrative_proposal": TemplateProfile(
        id="narrative_proposal",
        name="Narrative proposal",
        description="Long-form narrative with a warmer serif reading voice.",
        page_size="letter",
        margin_inches=0.9,
        body_font="Georgia",
        heading_font="Aptos Display",
        mono_font="Consolas",
        body_size=11,
        line_spacing=1.22,
        accent="#6D3AD7",
        text="#211B2A",
        muted="#6E6578",
    ),
}


def get_profile(profile_id: str) -> TemplateProfile:
    try:
        return PROFILES[profile_id]
    except KeyError as exc:
        raise ValueError(f"Unknown template: {profile_id}") from exc
