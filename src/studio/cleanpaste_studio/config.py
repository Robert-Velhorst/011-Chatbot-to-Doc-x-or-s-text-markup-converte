from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class Settings:
    data_dir: Path
    host: str = "127.0.0.1"
    port: int = 8765
    environment: str = "development"
    token: str | None = None
    max_source_bytes: int = 2_000_000
    rate_limit_per_minute: int = 60

    @property
    def production(self) -> bool:
        return self.environment.lower() == "production"

    @classmethod
    def from_env(cls) -> Settings:
        default_data = Path(os.environ.get("LOCALAPPDATA", ".")) / "AICleanPaste" / "studio"
        return cls(
            data_dir=Path(os.environ.get("CLEAN_PASTE_DATA_DIR", default_data)).resolve(),
            host=os.environ.get("CLEAN_PASTE_HOST", "127.0.0.1"),
            port=int(os.environ.get("CLEAN_PASTE_PORT", "8765")),
            environment=os.environ.get("CLEAN_PASTE_ENV", "development"),
            token=os.environ.get("CLEAN_PASTE_TOKEN") or None,
            max_source_bytes=int(os.environ.get("CLEAN_PASTE_MAX_SOURCE_BYTES", "2000000")),
            rate_limit_per_minute=int(os.environ.get("CLEAN_PASTE_RATE_LIMIT", "60")),
        )

    def validate(self) -> None:
        if self.production and not self.token:
            raise RuntimeError("CLEAN_PASTE_TOKEN is required in production mode")
        if self.host not in {"127.0.0.1", "localhost", "::1"} and not self.token:
            raise RuntimeError("A token is required when binding beyond loopback")
