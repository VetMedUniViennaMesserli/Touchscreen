from dataclasses import dataclass

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
    trainingName: str
