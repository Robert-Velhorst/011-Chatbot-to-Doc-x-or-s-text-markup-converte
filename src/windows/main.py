from __future__ import annotations

import threading

from clean_paste.agent import CleanPasteAgent, ClipboardNotificationWindow
from clean_paste.startup import set_startup, startup_enabled


def run() -> None:
    agent = CleanPasteAgent()
    try:
        import pystray  # type: ignore
        from PIL import Image, ImageDraw  # type: ignore

        image = Image.new("RGBA", (64, 64), (36, 99, 235, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((16, 14, 48, 50), outline="white", width=4)
        draw.line((23, 28, 41, 28), fill="white", width=3)
        draw.line((23, 37, 36, 37), fill="white", width=3)

        listener_ready = threading.Event()
        listener_holder: dict[str, ClipboardNotificationWindow] = {}

        def run_listener() -> None:
            listener = ClipboardNotificationWindow(agent)
            listener_holder["listener"] = listener
            listener_ready.set()
            listener.run()

        listener_thread = threading.Thread(target=run_listener, name="clipboard-listener", daemon=True)
        listener_thread.start()
        if not listener_ready.wait(timeout=5):
            raise RuntimeError("Clipboard listener did not start")

        def toggle(icon, _item) -> None:
            agent.enabled = not agent.enabled
            icon.title = f"AI Clean Paste — {'Enabled' if agent.enabled else 'Paused'}"
            icon.update_menu()

        def toggle_startup(_icon, _item) -> None:
            set_startup(not startup_enabled())

        def stop(icon, _item) -> None:
            listener_holder["listener"].stop()
            icon.stop()

        tray = pystray.Icon(
            "AICleanPaste", image, "AI Clean Paste — Enabled",
            menu=pystray.Menu(
                pystray.MenuItem(lambda _item: "Disable automatic formatting" if agent.enabled else "Enable automatic formatting", toggle),
                pystray.MenuItem("Start with Windows", toggle_startup, checked=lambda _item: startup_enabled()),
                pystray.MenuItem("Quit", stop),
            )
        )
        try:
            tray.run()
        finally:
            listener_holder["listener"].stop()
            listener_thread.join(timeout=5)
    except ImportError:
        ClipboardNotificationWindow(agent).run()


if __name__ == "__main__":
    run()
