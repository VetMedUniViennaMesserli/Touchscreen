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

def get_app_name() -> str:
    """Return the running app/example's own name (its folder's name, e.g.
    'RuleLearning' or 'TwoImages'), in both normal and frozen modes.

    Used as the default SessionLogs subfolder name so copying/renaming an
    app folder can't leave a stale, hand-typed trainingName behind.
    """
    if getattr(sys, 'frozen', False):
        return os.path.splitext(os.path.basename(sys.executable))[0]
    main = sys.modules.get('__main__')
    if main is not None and hasattr(main, '__file__'):
        return os.path.basename(os.path.dirname(os.path.abspath(main.__file__)))
    return 'UnknownApp'

def get_app_data_root() -> str:
    """Return a persistent, per-app directory for data that must survive
    across runs (e.g. individuals.csv) — unlike get_app_root(), which in
    frozen mode is a temp extraction dir wiped after every run.

    Frozen binary: a subfolder named after the executable, next to it
    (e.g. dist/RuleLearning/), so multiple built apps sharing one dist/
    folder don't collide.
    Normal run: the app's own folder — same as get_app_root() in this
    mode, which is already per-app and persistent (it's the real file in
    the working tree, not a temp copy).
    """
    if getattr(sys, 'frozen', False):
        return os.path.join(os.path.dirname(sys.executable), get_app_name())
    return get_app_root()

def get_log_root() -> str:
    """Return the directory where SessionLogs/ should be created.

    Frozen binary: next to the executable (e.g. dist/SessionLogs/).
    Normal run:    repo root (i.e. one level above Framework/).
    """
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.normpath(os.path.join(os.path.dirname(__file__), ".."))
