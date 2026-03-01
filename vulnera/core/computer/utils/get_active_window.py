import platform
import sys
import os


def is_termux():
    return (
        os.getenv("TERMUX_VERSION") is not None
        or os.getenv("PREFIX") == "/data/data/com.termux/files/usr"
        or os.path.isfile("/data/data/com.termux/files/usr/bin/termux-info")
    )


def get_active_window():
    if is_termux():
        # TERMUX_REVIEW: Termux doesn't typically support X11 window detection
        # Return None for now - may need X11 support if configured
        return None
    elif platform.system() == "Windows":
        import pygetwindow as gw

        win = gw.getActiveWindow()
        if win is not None:
            return {
                "region": (win.left, win.top, win.width, win.height),
                "title": win.title,
            }
    elif platform.system() == "Darwin":
        from AppKit import NSWorkspace
        from Quartz import (
            CGWindowListCopyWindowInfo,
            kCGNullWindowID,
            kCGWindowListOptionOnScreenOnly,
        )

        active_app = NSWorkspace.sharedWorkspace().activeApplication()
        for window in CGWindowListCopyWindowInfo(
            kCGWindowListOptionOnScreenOnly, kCGNullWindowID
        ):
            if window["kCGWindowOwnerName"] == active_app["NSApplicationName"]:
                return {
                    "region": window["kCGWindowBounds"],
                    "title": window.get("kCGWindowName", "Unknown"),
                }
    elif platform.system() == "Linux":
        from ewmh import EWMH
        from Xlib.display import Display

        ewmh = EWMH()
        win = ewmh.getActiveWindow()
        if win is not None:
            geom = win.get_geometry()
            return {
                "region": (geom.x, geom.y, geom.width, geom.height),
                "title": win.get_wm_name(),
            }
    else:
        print("Unsupported platform: ", platform.system())
        sys.exit(1)
