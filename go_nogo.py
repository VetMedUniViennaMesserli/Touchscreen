from Framework.ImageButton import ImageButton
from Framework.TrainingWindow import TrainingWindow
from Framework.TrainingImage import TrainingImage
from Framework.ImageCategory import ImageCategory
from Framework.SessionConfig import SessionConfig
from PySide6.QtWidgets import QApplication, QHBoxLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import sys
import random
import os

class GoNoGoTraining(TrainingWindow):
    def startFirstTrial(self):        
        self.layout = QHBoxLayout(self.container)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)

        self.trainingImage = self.getImage()

        self.button = ImageButton(self.trainingImage, self.imageClicked)
        self.layout.addWidget(self.button, alignment=Qt.AlignCenter)

        self.timeoutTimer = self.startFunctionTimer(2000, self.timeoutTrial)
        
        self.logTrialStart()

    def startNextTrial(self):
        self.trainingImage = self.getImage()

        self.button.changeImage(self.trainingImage)

        self.timeoutTimer = self.startFunctionTimer(2000, self.timeoutTrial)
        
        self.container.show()
        
        self.logTrialStart()
        
    def startCorrectionTrial(self):
        self.timeoutTimer = self.startFunctionTimer(2000, self.timeoutTrial)
        self.container.show()
        
        self.logTrialStart()

    def timeoutTrial(self):
        if self.trainingImage.imageCategory == ImageCategory.WRONG:
            self.trialCompletedSuccessful()
        elif self.trainingImage.imageCategory == ImageCategory.CORRECT:
            self.trialCompletedUnscucessful()

    def imageClicked(self, trainingImage: TrainingImage, event):
        self.timeoutTimer.stop()
        return super().imageClicked(trainingImage, event)

    def getImage(self):
        stimuli_path = os.path.join(os.path.dirname(__file__), "Training_Stimuli")
        image1 = os.path.join(stimuli_path, "Paintings", random.choice(os.listdir(os.path.join(stimuli_path, "Paintings"))))
        image2 = os.path.join(stimuli_path, "Underwater", random.choice(os.listdir(os.path.join(stimuli_path, "Underwater"))))

        trainingImages = [TrainingImage(image1, ImageCategory.CORRECT), TrainingImage(image2, ImageCategory.WRONG)]
        random.shuffle(trainingImages)

        return trainingImages[0]

def createTouchscreenWindow(sessionEndCallback=None):
    sessionConfig = SessionConfig(interTrialInterval=500,
                                  errorScreenDuration=500, 
                                  correctionTrialInterTrialInterval=500, 
                                  numberOfTrials=3, 
                                  correctionTrialsActive=True, 
                                  backgroundColor=QColor(255,255,255,255), 
                                  errorScreenColor=QColor(255,0,0,255), 
                                  successSoundFilePath=os.path.join(os.path.dirname(__file__), "SoundEffects", "600hz.wav"), 
                                  failureSoundFilePath=os.path.join(os.path.dirname(__file__), "SoundEffects", "200hz.wav"),
                                  cursorVisible=True,
                                  trainingName="Go-NoGo")

    trainingWindow = GoNoGoTraining(sessionConfig, sessionEndCallback=sessionEndCallback)

    trainingWindow.startFirstTrial()

    return trainingWindow

def startApp(sessionEndCallback = None):
    app = QApplication([])

    trainingWindow = createTouchscreenWindow()

    trainingWindow.showFullScreen()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    app = startApp()