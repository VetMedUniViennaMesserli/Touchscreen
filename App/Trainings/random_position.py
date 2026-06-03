from Framework.ImageButton import ImageButton
from Framework.TrainingWindow import TrainingWindow
from Framework.TrainingStimulus import TrainingStimulus
from Framework.StimulusCategory import StimulusCategory
from Framework.SessionConfig import SessionConfig
from PySide6.QtWidgets import QApplication, QGridLayout, QWidget, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import sys
import random
import os

class RandomPositionTraining(TrainingWindow):
    def startFirstTrial(self):
        self.layout = QGridLayout(self.container)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0, 0, 0, 0)

        self.cells = []
        for col in range(5):
            for row in range(4):
                cell = QWidget()
                QHBoxLayout(cell)
                self.layout.addWidget(cell, row, col, alignment=Qt.AlignCenter)
                self.cells.append(cell.layout())

        trainingImage = self.getImage()
        self._currentCellIndex = random.randrange(len(self.cells))
        self.imageButton = ImageButton(trainingImage, self.stimulusSelected, imageSize=(250, 250))
        self.cells[self._currentCellIndex].addWidget(self.imageButton, alignment=Qt.AlignCenter)

        self.logTrialStart()

    def startNextTrial(self):
        trainingImage = self.getImage()
        newCellIndex = random.randrange(len(self.cells))

        self.cells[self._currentCellIndex].takeAt(0)
        self.imageButton.changeImage(trainingImage)
        self.cells[newCellIndex].addWidget(self.imageButton, alignment=Qt.AlignCenter)
        self._currentCellIndex = newCellIndex

        self.container.show()
        self.container.update()
        self.logTrialStart()

    def startCorrectionTrial(self):
        self.container.show()
        self.logTrialStart()

    def getImage(self):
        stimuli_path = os.path.join(os.path.dirname(__file__), "..", "Training_Stimuli")
        image = os.path.join(stimuli_path, "Geometric_Shapes", random.choice(os.listdir(os.path.join(stimuli_path, "Geometric_Shapes"))))
        return TrainingStimulus(image, StimulusCategory.CORRECT)

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
                                  trainingName="Random Position")

    trainingWindow = RandomPositionTraining(sessionConfig, sessionEndCallback=sessionEndCallback)
    trainingWindow.startFirstTrial()
    return trainingWindow

def startApp():
    app = QApplication([])
    trainingWindow = createTouchscreenWindow()
    trainingWindow.showFullScreen()
    sys.exit(app.exec())

if __name__ == "__main__":
    startApp()
