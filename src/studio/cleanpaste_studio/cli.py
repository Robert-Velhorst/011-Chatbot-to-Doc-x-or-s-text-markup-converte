from __future__ import annotations

import argparse
import json
import sys
import tempfile
from dataclasses import replace
from pathlib import Path

import uvicorn

from .app import create_app
from .config import Settings
from .service import ConversionService
from .storage import StudioStorage
from .templates import PROFILES


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="clean-paste-studio", description="Local document conversion studio"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    serve = sub.add_parser("serve", help="Start the local Document Studio")
    serve.add_argument("--host", default=None)
    serve.add_argument("--port", type=int, default=None)

    convert = sub.add_parser("convert", help="Convert one source file")
    convert.add_argument("source", type=Path)
    convert.add_argument("--out", type=Path, required=True)
    convert.add_argument("--title")
    convert.add_argument(
        "--input-format", choices=["auto", "markdown", "html", "plain"], default="auto"
    )
    convert.add_argument("--formats", default="docx,pdf,markdown,text")
    convert.add_argument("--template", choices=sorted(PROFILES), default="standard_business_brief")

    sub.add_parser("doctor", help="Check local conversion prerequisites")
    return parser


def doctor() -> int:
    import shutil

    checks = {
        "python": sys.version.split()[0],
        "pdftoppm": shutil.which("pdftoppm") or "bundled lookup at runtime",
        "data_directory_writable": False,
    }
    settings = Settings.from_env()
    try:
        settings.data_dir.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=settings.data_dir):
            checks["data_directory_writable"] = True
    except OSError:
        pass
    print(json.dumps(checks, indent=2))
    return 0 if checks["data_directory_writable"] else 1


def convert_file(args) -> int:
    if not args.source.is_file():
        raise SystemExit(f"Source file not found: {args.source}")
    source = args.source.read_text(encoding="utf-8")
    title = args.title or args.source.stem
    requested = [value.strip() for value in args.formats.split(",") if value.strip()]
    args.out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="clean-paste-studio-") as temp:
        storage = StudioStorage(Path(temp))
        service = ConversionService(storage)
        project = service.create(title, source, args.input_format)
        result = service.generate(project["id"], requested, args.template)
        for artifact in result["artifacts"]:
            original = storage.artifact_path(project["id"], 1, artifact["name"])
            target = args.out / artifact["name"]
            target.write_bytes(original.read_bytes())
            artifact["path"] = str(target.resolve())
            verification = artifact.get("verification")
            preview_name = verification.get("preview_path") if verification else None
            if preview_name:
                preview_source = storage.version_dir(project["id"], 1) / "artifacts" / preview_name
                if preview_source.is_file():
                    preview_target = args.out / preview_name
                    preview_target.write_bytes(preview_source.read_bytes())
                    verification["preview_path"] = str(preview_target.resolve())
        print(json.dumps(result, indent=2))
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "doctor":
        return doctor()
    if args.command == "convert":
        return convert_file(args)
    settings = Settings.from_env()
    if args.host:
        settings = replace(settings, host=args.host)
    if args.port:
        settings = replace(settings, port=args.port)
    settings.validate()
    uvicorn.run(
        create_app(settings),
        host=settings.host,
        port=settings.port,
        log_config=None,
        access_log=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
