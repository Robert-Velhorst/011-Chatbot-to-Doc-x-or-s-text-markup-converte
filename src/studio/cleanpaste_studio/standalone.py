from __future__ import annotations

import multiprocessing
import os
import threading
import time
import urllib.request
import webbrowser
from pathlib import Path

import pystray
import uvicorn
from PIL import Image, ImageDraw


def _open_when_ready(url: str) -> None:
    for _ in range(80):
        try:
            with urllib.request.urlopen(f"{url}/health", timeout=1) as response:
                if response.status == 200:
                    webbrowser.open(url)
                    return
        except OSError:
            time.sleep(0.25)


def _tray_image() -> Image.Image:
    image = Image.new("RGB", (64, 64), "#0b1f3a")
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((12, 10, 52, 54), radius=6, fill="#ffffff")
    draw.rectangle((20, 20, 44, 24), fill="#2563eb")
    draw.rectangle((20, 31, 44, 35), fill="#16a34a")
    draw.rectangle((20, 42, 38, 46), fill="#2563eb")
    return image


def main() -> None:
    multiprocessing.freeze_support()
    local_app_data = Path(os.environ.get("LOCALAPPDATA", Path.home()))
    os.environ.setdefault("CLEAN_PASTE_DATA_DIR", str(local_app_data / "AI Clean Paste" / "Studio"))
    os.environ.setdefault("CLEAN_PASTE_HOST", "127.0.0.1")
    os.environ.setdefault("CLEAN_PASTE_PORT", "8765")

    from cleanpaste_studio.app import create_app
    from cleanpaste_studio.config import Settings

    settings = Settings.from_env()
    settings.validate()
    url = f"http://127.0.0.1:{settings.port}"
    server = uvicorn.Server(
        uvicorn.Config(
            create_app(settings),
            host=settings.host,
            port=settings.port,
            log_config=None,
            access_log=False,
        )
    )
    server_thread = threading.Thread(target=server.run, name="clean-paste-server", daemon=True)
    server_thread.start()
    threading.Thread(target=_open_when_ready, args=(url,), daemon=True).start()

    def open_studio(_icon=None, _item=None) -> None:
        webbrowser.open(url)

    def stop_studio(icon, _item=None) -> None:
        server.should_exit = True
        icon.stop()

    icon = pystray.Icon(
        "ai-clean-paste-studio",
        _tray_image(),
        "AI Clean Paste — Document Studio",
        menu=pystray.Menu(
            pystray.MenuItem("Open Document Studio", open_studio, default=True),
            pystray.MenuItem("Stop", stop_studio),
        ),
    )
    try:
        icon.run()
    finally:
        server.should_exit = True
        server_thread.join(timeout=10)


if __name__ == "__main__":
    main()
