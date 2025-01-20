from Framework.ImageButton import ImageButton
from Framework.TrainingWindow import TrainingWindow
from Framework.TrainingImage import TrainingImage
from Framework.ImageCategory import ImageCategory
from Framework.SessionConfig import SessionConfig
from PySide6.QtWidgets import QApplication, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import sys
import copy
import os

class SequentialLearningTraining(TrainingWindow):
    def startFirstTrial(self):        
        self.layout = QGridLayout(self.container)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(450,300,450,300)

        self.trainingImages = self.getImages()
        self.buttons = []
        
        self.buttons.append(ImageButton(self.trainingImages[0], self.imageClicked, (150, 150)))
        self.buttons.append(ImageButton(self.trainingImages[1], self.imageClicked, (150, 150)))
        self.buttons.append(ImageButton(self.trainingImages[2], self.imageClicked, (150, 150)))
        self.buttons.append(ImageButton(self.trainingImages[3], self.imageClicked, (150, 150)))
        self.buttons.append(ImageButton(self.trainingImages[4], self.imageClicked, (150, 150)))
        self.buttons.append(ImageButton(self.trainingImages[5], self.imageClicked, (150, 150)))
        self.buttons.append(ImageButton(self.trainingImages[6], self.imageClicked, (150, 150)))
        self.buttons.append(ImageButton(self.trainingImages[7], self.imageClicked, (150, 150)))
        
        self.layout.addWidget(self.buttons[0], 1, 0, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.buttons[1], 1, 1, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.buttons[2], 1, 2, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.buttons[3], 1, 3, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.buttons[4], 0, 3, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.buttons[5], 0, 2, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.buttons[6], 0, 1, alignment=Qt.AlignCenter)
        self.layout.addWidget(self.buttons[7], 0, 0, alignment=Qt.AlignCenter)

        self.sequenceIndex = 0
        
        self.logTrialStart()

    def imageClicked(self, trainingImage: TrainingImage, event):
        result = super().imageClicked(trainingImage, event)
    
        if trainingImage == self.trainingImages[self.sequenceIndex]:
            if self.sequenceIndex == 7:
                self.trialCompletedSuccessful()
            else:
                self.buttons[self.sequenceIndex].changeImage(None)
                self.sequenceIndex += 1
        elif trainingImage is not None:
            self.trialCompletedUnscucessful()

        return result

    def startNextTrial(self):
        self.trainingImages = self.getImages()
        
        self.buttons[0].changeImage(self.trainingImages[0])
        self.buttons[1].changeImage(self.trainingImages[1])
        self.buttons[2].changeImage(self.trainingImages[2])
        self.buttons[3].changeImage(self.trainingImages[3])
        self.buttons[4].changeImage(self.trainingImages[4])
        self.buttons[5].changeImage(self.trainingImages[5])
        self.buttons[6].changeImage(self.trainingImages[6])
        self.buttons[7].changeImage(self.trainingImages[7])
        
        self.sequenceIndex = 0

        self.container.show()

        self.logTrialStart()
        
    def startCorrectionTrial(self):
        self.trainingImages = self.getImages()

        self.buttons[0].changeImage(self.trainingImages[0])
        self.buttons[1].changeImage(self.trainingImages[1])
        self.buttons[2].changeImage(self.trainingImages[2])
        self.buttons[3].changeImage(self.trainingImages[3])
        self.buttons[4].changeImage(self.trainingImages[4])
        self.buttons[5].changeImage(self.trainingImages[5])
        self.buttons[6].changeImage(self.trainingImages[6])
        self.buttons[7].changeImage(self.trainingImages[7])
        
        self.sequenceIndex = 0

        self.container.show()
        
        self.logTrialStart()

    def getImages(self):
        image = os.path.join(os.path.dirname(__file__), "Training_Stimuli", "Geometric_Shapes", "Circle_Red.png")

        trainingImage = TrainingImage(image, ImageCategory.OTHER)

        trainingImages = []

        for i in range(8):
            trainingImages.append(copy.copy(trainingImage))

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
                                  trainingName="Sequential Learning")

    trainingWindow = SequentialLearningTraining(sessionConfig, sessionEndCallback=sessionEndCallback)

    trainingWindow.startFirstTrial()

    return trainingWindow

def startApp(sessionEndCallback = None):
    app = QApplication([])

    trainingWindow = createTouchscreenWindow()

    trainingWindow.showFullScreen()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    app = startApp()