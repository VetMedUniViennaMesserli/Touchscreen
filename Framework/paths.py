import sys
import os

def get_app_root() -> str:
    """Return the directory of the running app (where its own
    Training_Stimuli/ and SoundEffects/ live), in both normal and
    PyInstaller frozen modes.

    Each app/example owns its assets rather than sharing one pool, so this
    resolves relative to the entry script that was actually launched
    (sys.modules['__main__']), not relative to Framework/ itself.
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    main = sys.modules.get('__main__')
    if main is not None and hasattr(main, '__file__'):
        return os.path.dirname(os.path.abspath(main.__file__))
    return os.getcwd()

def get_log_root() -> str:
    """Return the directory where SessionLogs/ should be created.

    Frozen binary: next to the executable (e.g. dist/SessionLogs/).
    Normal run:    repo root (i.e. one level above Framework/).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
