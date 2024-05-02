from Framework.ImageButton import ImageButton
from Framework.TrainingWindow import TrainingWindow
from Framework.TrainingImage import TrainingImage
from Framework.ImageCategory import ImageCategory
from Framework.SessionConfig import SessionConfig
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
        
        self.button0 = ImageButton(correctImage, self.imageClicked, imageSize=(250,250))
        self.exampleImagesLayout.addWidget(self.button0, alignment=Qt.AlignCenter)

        self.button1 = ImageButton(trainingImages[0], self.imageClicked, imageSize=(250,250))
        self.button2 = ImageButton(trainingImages[1], self.imageClicked, imageSize=(250,250))
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
        images = random.sample(os.listdir(os.path.join("Training_Stimuli", "Geometric_Shapes")), 2)
        correctImage = random.choice(images)

        trainingImages= []
        
        for image in images:
            if image == correctImage:
                trainingImages.append(TrainingImage(os.path.join("Training_Stimuli", "Geometric_Shapes", image), ImageCategory.CORRECT))
            else:
                trainingImages.append(TrainingImage(os.path.join("Training_Stimuli", "Geometric_Shapes", image), ImageCategory.WRONG))

        random.shuffle(trainingImages)

        return TrainingImage(os.path.join("Training_Stimuli", "Geometric_Shapes", correctImage), ImageCategory.OTHER), trainingImages

if __name__ == "__main__":
    app = QApplication([])

    sessionConfig = SessionConfig(interTrialInterval=2000,
                                  errorScreenDuration=1000, 
                                  correctionTrialInterTrialInterval=1000, 
                                  numberOfTrials=5, 
                                  correctionTrialsActive=True, 
                                  backgroundColor=QColor(100,100,100,255), 
                                  errorScreenColor=QColor(255,0,0,255), 
                                  successSoundFilePath=os.path.join("SoundEffects", "600hz.wav"), 
                                  failureSoundFilePath=os.path.join("SoundEffects", "200hz.wav"),
                                  cursorVisible=True,
                                  trainingName="Matching to Sample")

    trainingWindow = MatchingToSampleTraining(sessionConfig)
    
    trainingWindow.startFirstTrial()

    trainingWindow.showFullScreen()
    
    sys.exit(app.exec())