from Framework.ImageButton import ImageButton
from Framework.TrainingWindow import TrainingWindow
from Framework.TrainingStimulus import TrainingStimulus
from Framework.StimulusCategory import StimulusCategory
from Framework.SessionConfig import SessionConfig
from Framework.paths import get_app_root
from PySide6.QtWidgets import QApplication, QHBoxLayout, QWidget
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
import sys
import random
import os

class MatchingToSampleTraining(TrainingWindow):
    def startFirstTrial(self):        
        self.layout = QHBoxLayout(self.container)
        self.layout.setSpacing(0)
        self.layout.setContentsMargins(0,0,0,0)

        self.exampleImages = QWidget()
        self.exampleImagesLayout = QHBoxLayout(self.exampleImages)
        self.exampleImagesLayout.setSpacing(0)
        self.exampleImagesLayout.setContentsMargins(0,0,0,0)
        
        self.decisionImages = QWidget()
        self.decisionImagesLayout = QHBoxLayout(self.decisionImages)
        self.decisionImagesLayout.setSpacing(0)
        self.decisionImagesLayout.setContentsMargins(0,0,0,0)

        self.layout.addWidget(self.exampleImages)
        self.layout.addWidget(self.decisionImages)

        self.exampleImages.show()
        self.decisionImages.hide()

        correctImage, trainingImages = self.getImages()
        
        self.button0 = ImageButton(correctImage, self.stimulusSelected, imageSize=(250,250))
        self.exampleImagesLayout.addWidget(self.button0, alignment=Qt.AlignCenter)

        self.button1 = ImageButton(trainingImages[0], self.stimulusSelected, imageSize=(250,250))
        self.button2 = ImageButton(trainingImages[1], self.stimulusSelected, imageSize=(250,250))
        self.decisionImagesLayout.addWidget(self.button1, alignment=Qt.AlignCenter)
        self.decisionImagesLayout.addWidget(self.button2, alignment=Qt.AlignCenter)

        self.startFunctionTimer(1000, self.showDecisionImages)
        
        self.logTrialStart()

    def showDecisionImages(self):
        self.exampleImages.hide()
        self.decisionImages.show()

    def startNextTrial(self):
        correctImage, trainingImages = self.getImages()
        
        self.button0.changeImage(correctImage)
        self.button1.changeImage(trainingImages[0])
        self.button2.changeImage(trainingImages[1])

        self.exampleImages.show()
        self.decisionImages.hide()
        self.startFunctionTimer(1000, self.showDecisionImages)

        self.container.show()
        
        self.logTrialStart()
        
    def startCorrectionTrial(self):
        self.exampleImages.show()
        self.decisionImages.hide()
        self.startFunctionTimer(1000, self.showDecisionImages)

        self.container.show()
        
        self.logTrialStart()

    def getImages(self):
        stimuli_path = os.path.join(get_app_root(),"Training_Stimuli", "Geometric_Shapes")
        images = random.sample(os.listdir(stimuli_path), 2)
        correctImage = random.choice(images)

        trainingImages= []
        
        for image in images:
            if image == correctImage:
                trainingImages.append(TrainingStimulus(os.path.join(stimuli_path, image), StimulusCategory.CORRECT))
            else:
                trainingImages.append(TrainingStimulus(os.path.join(stimuli_path, image), StimulusCategory.WRONG))

        random.shuffle(trainingImages)

        return TrainingStimulus(os.path.join(stimuli_path, correctImage), StimulusCategory.OTHER), trainingImages

def createTouchscreenWindow(sessionEndCallback=None):
    sessionConfig = SessionConfig(interTrialInterval=2000,
                                  errorScreenDuration=1000, 
                                  correctionTrialInterTrialInterval=1000, 
                                  numberOfTrials=5, 
                                  correctionTrialsActive=True, 
                                  backgroundColor=QColor(100,100,100,255), 
                                  errorScreenColor=QColor(255,0,0,255), 
                                  successSoundFilePath=os.path.join(get_app_root(),"SoundEffects", "600hz.wav"), 
                                  failureSoundFilePath=os.path.join(get_app_root(),"SoundEffects", "200hz.wav"),
                                  cursorVisible=True,
                                  trainingName="Matching to Sample")

    trainingWindow = MatchingToSampleTraining(sessionConfig, sessionEndCallback=sessionEndCallback)

    trainingWindow.startFirstTrial()

    return trainingWindow

def startApp():
    app = QApplication([])

    trainingWindow = createTouchscreenWindow()

    trainingWindow.showFullScreen()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    app = startApp()