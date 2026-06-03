import sys
import os

def get_app_root() -> str:
    """Return the App/ directory in both normal and PyInstaller frozen modes."""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    return os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))

def get_log_root() -> str:
    """Return the directory where SessionLogs/ should be created.

    Frozen binary: next to the executable (e.g. dist/SessionLogs/).
    Normal run:    repo root (i.e. two levels above Framework/).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.normpath(os.path.join(os.path.dirname(__file__), "..", ".."))
