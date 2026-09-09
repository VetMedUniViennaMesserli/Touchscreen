from Framework.TrainingStimulus import TrainingStimulus
from Framework.ImageStimulusDisplay import ImageStimulusDisplay

class ImageButton(ImageStimulusDisplay):
    def __init__(self, trainingImage: TrainingStimulus, stimulusSelected, imageSize=None, parent=None):
        super(ImageButton, self).__init__(trainingImage, imageSize, parent)
        self.stimulusSelected = stimulusSelected

    def mousePressEvent(self, e):
        if self.trainingImage is not None:
            self.stimulusSelected(self.trainingImage)
        super().mousePressEvent(e)