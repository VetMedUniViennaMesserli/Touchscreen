class SessionConfig():
    def __init__(self, 
                 interTrialInterval: int,
                 errorScreenDuration: int,
                 correctionTrialInterTrialInterval:int,
                 numberOfTrials: int, 
                 correctionTrialsActive: bool,
                 backgroundColor, 
                 errorScreenColor,
                 successSoundFilePath,
                 failureSoundFilePath,
                 cursorVisible: bool,
                 trainingName):
        self.interTrialInterval = interTrialInterval
        self.errorScreenDuration = errorScreenDuration
        self.correctionTrialInterTrialInterval = correctionTrialInterTrialInterval
        self.numberOfTrials = numberOfTrials
        self.correctionTrialsActive = correctionTrialsActive
        self.backgroundColor = backgroundColor
        self.errorScreenColor = errorScreenColor
        self.successSoundFilePath = successSoundFilePath
        self.failureSoundFilePath = failureSoundFilePath
        self.cursorVisible = cursorVisible
        self.trainingName = trainingName