from Framework.StimulusCategory import StimulusCategory

class TrainingStimulus():
    
    def __init__(self, filePath, category: StimulusCategory):
        self.filePath = filePath
        self.stimulusCategory = category