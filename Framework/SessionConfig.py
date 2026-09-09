from dataclasses import dataclass
from typing import Optional

@dataclass
class SessionConfig:
    interTrialInterval: int
    errorScreenDuration: int
    correctionTrialInterTrialInterval: int
    numberOfTrials: int
    correctionTrialsActive: bool
    backgroundColor: object
    errorScreenColor: object
    successSoundFilePath: str
    failureSoundFilePath: str
    cursorVisible: bool
    # Defaults to the running app's own folder name (see
    # Framework.paths.get_app_name()) if not set explicitly — only pass
    # this if an app genuinely needs a SessionLogs folder name that
    # differs from its own folder name.
    trainingName: Optional[str] = None
