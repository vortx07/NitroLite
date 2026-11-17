"""
NitroLite - Ultra-Lightweight Acer Nitro Management Dashboard
Main application entry point.
"""

import sys
import argparse
import socket
from backend import AcerNitroController
from gui import NitroLiteApp


def ensure_single_instance(port: int = 49152) -> socket.socket:
    """Ensure only one instance of NitroLite runs at a time."""
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(("127.0.0.1", port))
        s.listen(1)
        return s
    except socket.error:
        print("[!] NitroLite is already running in the background/system tray.")
        sys.exit(0)


def main():
    parser = argparse.ArgumentParser(description="NitroLite - Lightweight Acer Nitro Controller")
    parser.add_argument("--tray", "--minimized", action="store_true", help="Start minimized to system tray")
    args = parser.parse_args()

    # Prevent duplicate instances
    _instance_lock = ensure_single_instance()

    print("[*] Starting NitroLite...")
    controller = AcerNitroController()

    app = NitroLiteApp(controller, start_minimized=args.tray)
    try:
        app.mainloop()
    except KeyboardInterrupt:
        app.quit_app()


if __name__ == "__main__":
    main()
