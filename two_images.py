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

class TwoImagesTraining(TrainingWindow):
    def startFirstTrial(self):        
        self.layout = QHBoxLayout(self.container)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)

        trainingImages = self.getImages()

        self.button1 = ImageButton(trainingImages[0], self.imageClicked)
        self.button2 = ImageButton(trainingImages[1], self.imageClicked)
        self.layout.addWidget(self.button1, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.button2, alignment=Qt.AlignCenter)
        
        self.logTrialStart()

    def startNextTrial(self):
        trainingImages = self.getImages()
        
        self.button1.changeImage(trainingImages[0])
        self.button2.changeImage(trainingImages[1])
        self.container.show()
        
        self.logTrialStart()
        
    def startCorrectionTrial(self):
        self.container.show()
        
        self.logTrialStart()

    def getImages(self):
        stimuli_path = os.path.join(os.path.dirname(__file__), "Training_Stimuli")
        image1 = os.path.join(stimuli_path, "Paintings", random.choice(os.listdir(os.path.join(stimuli_path, "Paintings"))))
        image2 = os.path.join(stimuli_path, "Underwater", random.choice(os.listdir(os.path.join(stimuli_path, "Underwater"))))

        trainingImages = [TrainingImage(image1, ImageCategory.CORRECT), TrainingImage(image2, ImageCategory.WRONG)]
        random.shuffle(trainingImages)

        return trainingImages

def createTouchscreenWindow(sessionEndCallback=None):
    sessionConfig = SessionConfig(interTrialInterval=2000,
                                  errorScreenDuration=1000, 
                                  correctionTrialInterTrialInterval=1000, 
                                  numberOfTrials=5, 
                                  correctionTrialsActive=True, 
                                  backgroundColor=QColor(255,255,255,255), 
                                  errorScreenColor=QColor(255,0,0,255), 
                                  successSoundFilePath=os.path.join(os.path.dirname(__file__), "SoundEffects", "600hz.wav"), 
                                  failureSoundFilePath=os.path.join(os.path.dirname(__file__), "SoundEffects", "200hz.wav"),
                                  cursorVisible=True,
                                  trainingName="Two Images")

    trainingWindow = TwoImagesTraining(sessionConfig, sessionEndCallback=sessionEndCallback)

    trainingWindow.startFirstTrial()

    return trainingWindow

def startApp(sessionEndCallback = None):
    app = QApplication([])

    trainingWindow = createTouchscreenWindow()

    trainingWindow.showFullScreen()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    app = startApp()