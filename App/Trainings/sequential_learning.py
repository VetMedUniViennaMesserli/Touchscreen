from Framework.ImageButton import ImageButton
from Framework.TrainingWindow import TrainingWindow
from Framework.TrainingStimulus import TrainingStimulus
from Framework.StimulusCategory import StimulusCategory
from Framework.SessionConfig import SessionConfig
from PySide6.QtWidgets import QApplication, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import sys
import copy
import os

class SequentialLearningTraining(TrainingWindow):
    # Positions in the grid: (row, col) for buttons 0-7, forming a U-shape
    _POSITIONS = [(1,0),(1,1),(1,2),(1,3),(0,3),(0,2),(0,1),(0,0)]

    def startFirstTrial(self):
        self.layout = QGridLayout(self.container)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(450, 300, 450, 300)

        self.trainingImages = self.getImages()
        self.buttons = []
        for i, (row, col) in enumerate(self._POSITIONS):
            btn = ImageButton(self.trainingImages[i], self.stimulusSelected, (150, 150))
            self.buttons.append(btn)
            self.layout.addWidget(btn, row, col, alignment=Qt.AlignCenter)

        self.sequenceIndex = 0
        self.logTrialStart()

    def stimulusSelected(self, trainingImage: TrainingStimulus):
        self.logStimulusSelected(trainingImage)
        if trainingImage == self.trainingImages[self.sequenceIndex]:
            if self.sequenceIndex == len(self.buttons) - 1:
                self.trialCompletedSuccessful()
            else:
                self.buttons[self.sequenceIndex].changeImage(None)
                self.sequenceIndex += 1
        else:
            self.trialCompletedUnsuccessful()

    def _resetTrial(self):
        self.trainingImages = self.getImages()
        for i, btn in enumerate(self.buttons):
            btn.changeImage(self.trainingImages[i])
        self.sequenceIndex = 0
        self.container.show()
        self.logTrialStart()

    def startNextTrial(self):
        self._resetTrial()

    def startCorrectionTrial(self):
        self._resetTrial()

    def getImages(self):
        image = os.path.join(os.path.dirname(__file__), "..", "Training_Stimuli", "Geometric_Shapes", "Circle_Red.png")
        trainingImage = TrainingStimulus(image, StimulusCategory.OTHER)
        return [copy.copy(trainingImage) for _ in range(len(self._POSITIONS))]

def createTouchscreenWindow(sessionEndCallback=None):
    sessionConfig = SessionConfig(interTrialInterval=2000,
                                  errorScreenDuration=1000,
                                  correctionTrialInterTrialInterval=1000,
                                  numberOfTrials=5,
                                  correctionTrialsActive=True,
                                  backgroundColor=QColor(255,255,255,255),
                                  errorScreenColor=QColor(255,0,0,255),
                                  successSoundFilePath=os.path.join(os.path.dirname(__file__), "..", "SoundEffects", "600hz.wav"),
                                  failureSoundFilePath=os.path.join(os.path.dirname(__file__), "..", "SoundEffects", "200hz.wav"),
                                  cursorVisible=True,
                                  trainingName="Sequential Learning")

    trainingWindow = SequentialLearningTraining(sessionConfig, sessionEndCallback=sessionEndCallback)
    trainingWindow.startFirstTrial()
    return trainingWindow

def startApp():
    app = QApplication([])
    trainingWindow = createTouchscreenWindow()
    trainingWindow.showFullScreen()
    sys.exit(app.exec())

if __name__ == "__main__":
    startApp()
