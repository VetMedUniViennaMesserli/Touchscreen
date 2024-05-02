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
        image1 = os.path.join("Training_Stimuli", "Paintings", random.choice(os.listdir(os.path.join("Training_Stimuli", "Paintings"))))
        image2 = os.path.join("Training_Stimuli", "Underwater", random.choice(os.listdir(os.path.join("Training_Stimuli", "Underwater"))))

        trainingImages = [TrainingImage(image1, ImageCategory.CORRECT), TrainingImage(image2, ImageCategory.WRONG)]
        random.shuffle(trainingImages)

        return trainingImages[0]

if __name__ == "__main__":
    app = QApplication([])

    sessionConfig = SessionConfig(interTrialInterval=2000,
                                  errorScreenDuration=1000, 
                                  correctionTrialInterTrialInterval=1000, 
                                  numberOfTrials=5, 
                                  correctionTrialsActive=True, 
                                  backgroundColor=QColor(255,255,255,255), 
                                  errorScreenColor=QColor(255,0,0,255), 
                                  successSoundFilePath=os.path.join("SoundEffects", "600hz.wav"), 
                                  failureSoundFilePath=os.path.join("SoundEffects", "200hz.wav"),
                                  cursorVisible=True,
                                  trainingName="Go-NoGo")

    trainingWindow = GoNoGoTraining(sessionConfig)
    
    trainingWindow.startFirstTrial()

    trainingWindow.showFullScreen()
    
    sys.exit(app.exec())